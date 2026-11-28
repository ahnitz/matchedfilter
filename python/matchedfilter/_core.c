#include <string.h>
/* matchedfilter Python extension: the matched filter.
 *
 * The whole D x T pair loop happens in one call into C, so no per-pair Python
 * overhead reaches the measurement.  Only the matched filter is exposed: there is
 * no transform plan to hand out, because callers bring their own spectra. */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <limits.h>
#include "matchedfilter.h"
#include "transform.h"
#include "q15.h"
#include "alloc.h"
#include "simulate.h"
#include "followup.h"

/* Whether a buffer of len bytes holds a x b elements of elem bytes, computed by division:
   the product of caller-supplied counts can overflow, and the check then passes. */
static int buf_holds(Py_ssize_t len,Py_ssize_t a,Py_ssize_t b,Py_ssize_t elem){
  if(a<0||b<0||elem<=0||len<0) return 0;
  if(a==0||b==0) return 1;
  return len/elem/a >= b;
}

#include <time.h>

/* Validate the extension boundary independently of the Python convenience API.
   Divide byte capacities instead of multiplying untrusted sizes. */
typedef struct {
  int64_t index;
  float re, im;
} ap_structured_peak;

static int output_shape(Py_ssize_t rows,size_t nb,Py_buffer *ix,Py_buffer *val,
                        Py_buffer *mag,Py_buffer *cnt,Py_buffer *spk,Py_ssize_t *need){
  if(rows<1 || nb<1 || nb>(size_t)PY_SSIZE_T_MAX/(size_t)rows){
    PyErr_SetString(PyExc_ValueError,"invalid or overflowing output shape"); return 0;
  }
  *need=rows*(Py_ssize_t)nb;
  if(*need>PY_SSIZE_T_MAX/(Py_ssize_t)sizeof(ap_peak)){
    PyErr_SetString(PyExc_ValueError,"output arrays too small or output shape overflows"); return 0;
  }
  int have_spk = (spk && spk->buf && spk->len);
  if(have_spk){
    if(spk->len/16 < *need){
      PyErr_SetString(PyExc_ValueError,"output arrays too small or output shape overflows"); return 0;
    }
  } else {
    if(ix->len/8<*need || val->len/8<*need){
      PyErr_SetString(PyExc_ValueError,"output arrays too small or output shape overflows"); return 0;
    }
  }
  if((mag->len && mag->len/4<*need) || cnt->len/4<rows){
    PyErr_SetString(PyExc_ValueError,"output arrays too small or output shape overflows"); return 0;
  }
  return 1;
}
static int run_shape(Py_ssize_t n,int maxd,int maxt,int d0,int nd,int t0,int nt,
                     Py_ssize_t bs,Py_ssize_t start,Py_ssize_t end,
                     size_t *nb,Py_ssize_t *rows){
  if(d0<0 || nd<1 || nd>maxd || d0>maxd-nd || t0<0 || nt<1
     || nt>maxt || t0>maxt-nt || bs<1 || start<0 || end<=start || start>=n){
    PyErr_SetString(PyExc_ValueError,"invalid subrange, binsize or window"); return 0;
  }
  if(end>n) end=n;
  *nb=1+(size_t)(end-start-1)/(size_t)bs;
  if((Py_ssize_t)nd>PY_SSIZE_T_MAX/nt){
    PyErr_SetString(PyExc_ValueError,"pair count overflows"); return 0;
  }
  *rows=(Py_ssize_t)nd*nt;
  return 1;
}
/* A block layout's bin phases (run_series' bin_phase): uint32 per block, each below 2^24 (a
   bound on the bins it can add); no buffer (ph->buf NULL) is every phase 0. */
static int phase_ok(const Py_buffer *ph,int blocks,Py_ssize_t binsize){
  if(!ph || !ph->buf) return 1;
  if(ph->len!=(Py_ssize_t)blocks*(Py_ssize_t)sizeof(unsigned)){
    PyErr_SetString(PyExc_ValueError,"bin_phase needs one uint32 per block"); return 0;
  }
  const unsigned *v=ph->buf;
  (void)binsize;
  for(int i=0;i<blocks;i++) if(v[i]>=(1u<<24)){
    PyErr_SetString(PyExc_ValueError,"bin_phase must be below 2**24"); return 0;
  }
  return 1;
}
static const unsigned *phase_of(const Py_buffer *ph){ return ph && ph->buf ? ph->buf : NULL; }
/* The optional bin_phase argument: None (or absent) for none. */
static int phase_arg(PyObject *o,Py_buffer *ph){
  ph->buf=NULL;
  if(!o || o==Py_None) return 1;
  return PyObject_GetBuffer(o,ph,PyBUF_C_CONTIGUOUS)==0;
}
static void phase_release(Py_buffer *ph){ if(ph->buf) PyBuffer_Release(ph); ph->buf=NULL; }

/* real: the series is real float32 samples (HMF set_real_series), else complex64. ph: the
   blocks' bin phases (or no buffer), which set each block's bin count. */
static int series_shape_r(Py_ssize_t n,int maxt,int t0,int nt,Py_ssize_t binsize,int real,
                          Py_buffer *ser,Py_buffer *st,Py_buffer *ws,Py_buffer *we,
                          const Py_buffer *ph,int *blocks,size_t *nb,Py_ssize_t *rows){
  const Py_ssize_t unit=(Py_ssize_t)sizeof(size_t);
  if(ser->len%(real?4:8) || st->len<unit || st->len%unit || st->len/unit>INT_MAX
     || ws->len!=st->len || we->len!=st->len){
    PyErr_SetString(PyExc_ValueError,"invalid series or block-layout buffer lengths"); return 0;
  }
  *blocks=(int)(st->len/unit);
  if(!phase_ok(ph,*blocks,binsize)) return 0;
  const unsigned *phv=phase_of(ph);
  const size_t *starts=st->buf,*lo=ws->buf,*hi=we->buf;
  size_t first=0;
  for(int i=0;i<*blocks;i++){
    if(starts[i]>SIZE_MAX-(size_t)n || lo[i]>(size_t)PY_SSIZE_T_MAX
       || hi[i]>(size_t)PY_SSIZE_T_MAX){
      PyErr_SetString(PyExc_ValueError,"block offset or window overflows"); return 0;
    }
    Py_ssize_t ignored;
    size_t bins;
    if(!run_shape(n,1,maxt,0,1,t0,nt,binsize,(Py_ssize_t)lo[i],
                  (Py_ssize_t)hi[i],&bins,&ignored)) return 0;
    if(phv) bins=ap_bin_count((size_t)binsize,lo[i],hi[i]>(size_t)n?(size_t)n:hi[i],phv[i]);
    if(i && bins!=first){
      PyErr_SetString(PyExc_ValueError,"block windows must have equal bin counts"); return 0;
    }
    first=bins;
  }
  if((Py_ssize_t)*blocks>PY_SSIZE_T_MAX/nt){
    PyErr_SetString(PyExc_ValueError,"pair count overflows"); return 0;
  }
  *nb=first; *rows=(Py_ssize_t)*blocks*nt; return 1;
}
static int series_shape_dif(Py_ssize_t n,int maxt,int t0,int nt,Py_ssize_t binsize,
                            int decimated,
                            Py_buffer *ser,Py_buffer *st,Py_buffer *ws,Py_buffer *we,
                            const Py_buffer *ph,int *blocks,size_t *nb,Py_ssize_t *rows){
  const Py_ssize_t unit=(Py_ssize_t)sizeof(size_t);
  if(ser->len%8 || st->len<unit || st->len%unit || st->len/unit>INT_MAX
     || ws->len!=st->len || we->len!=st->len){
    PyErr_SetString(PyExc_ValueError,"invalid series or block-layout buffer lengths"); return 0;
  }
  if(t0<0 || nt<1 || nt>maxt || t0>maxt-nt || binsize<1){
    PyErr_SetString(PyExc_ValueError,"invalid template subrange or binsize"); return 0;
  }
  *blocks=(int)(st->len/unit);
  if(!phase_ok(ph,*blocks,binsize)) return 0;
  const unsigned *phv=phase_of(ph);
  const size_t *starts=st->buf,*lo=ws->buf,*hi=we->buf;
  const size_t N = decimated ? (size_t)n : (size_t)(2 * n);
  size_t first=0;
  for(int i=0;i<*blocks;i++){
    if(starts[i]>SIZE_MAX-N || lo[i]>(size_t)PY_SSIZE_T_MAX
       || hi[i]>(size_t)PY_SSIZE_T_MAX || lo[i]>=hi[i] || lo[i]>=N){
      PyErr_SetString(PyExc_ValueError,"block offset or window overflows / invalid"); return 0;
    }
    size_t w_end = hi[i] > N ? N : hi[i];
    size_t bins = ap_bin_count((size_t)binsize, lo[i], w_end, phv ? phv[i] : 0u);
    if(i && bins!=first){
      PyErr_SetString(PyExc_ValueError,"block windows must have equal bin counts"); return 0;
    }
    first=bins;
  }
  if((Py_ssize_t)*blocks>PY_SSIZE_T_MAX/nt){
    PyErr_SetString(PyExc_ValueError,"pair count overflows"); return 0;
  }
  *nb=first; *rows=(Py_ssize_t)*blocks*nt; return 1;
}
static ap_peak *reserve_peaks(ap_peak **storage,Py_ssize_t *capacity,Py_ssize_t need){
  if(need>*capacity){
    ap_peak *next=PyMem_Realloc(*storage,(size_t)need*sizeof(ap_peak));
    if(!next){ PyErr_NoMemory(); return NULL; }
    *storage=next; *capacity=need;
  }
  return *storage;
}

/* ---------------- ingest, run and run_series, shared by MF and HMF ---------------- */
/* What these bindings read of a filter object: its plan and which engine it is (hier: an
   ap_hmf_plan, else an ap_mf_plan), the samples per data spectrum (n) and per template
   spectrum (k), the data and template rows, the reusable peak table, and whether
   run_series reads a real series (HMF set_real_series) with real_stride floats between
   samples. mf_view and hmf_view build it. */
typedef struct {
  void *p; int hier; Py_ssize_t n,k; int nd,nt;
  ap_peak **peaks; Py_ssize_t *capacity; int real,real_stride;
} filter_view;

/* Spectrum spec into data row i (is_data) or template row i: 0, or -1 for a bad row. */
static int set_spectrum(const filter_view *f,int is_data,int i,const float *spec){
  if(f->hier) return is_data ? ap_hmf_set_data(f->p,i,spec) : ap_hmf_set_template(f->p,i,spec);
  return is_data ? ap_mf_set_data(f->p,i,spec) : ap_mf_set_template(f->p,i,spec);
}
/* set_data(i, buffer) and set_template(i, buffer): row i's spectrum, n (data) or k
   (template) complex64 samples, copied in. Returns None. */
static PyObject *bind_set(filter_view f,PyObject *args,int is_data){
  int i; Py_buffer b;
  if(!PyArg_ParseTuple(args,"iy*",&i,&b)) return NULL;
  const Py_ssize_t len = is_data ? f.n : f.k;
  if(b.len < len*2*(Py_ssize_t)sizeof(float)){
    PyBuffer_Release(&b);
    return PyErr_Format(PyExc_ValueError,"segment must hold %zd complex64 samples",len);
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r = set_spectrum(&f,is_data,i,(const float*)b.buf);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b);
  if(r<0) return PyErr_Format(PyExc_IndexError,"index %d out of range",i);
  Py_RETURN_NONE;
}
/* set_data_batch(i0, buffer) and set_template_batch(i0, buffer): rows i0, i0+1, ..., one per
   whole spectrum the buffer holds. Returns None. */
static PyObject *bind_set_batch(filter_view f,PyObject *args,int is_data){
  int i0; Py_buffer b;
  if(!PyArg_ParseTuple(args,"iy*",&i0,&b)) return NULL;
  const Py_ssize_t len = is_data ? f.n : f.k;
  Py_ssize_t rowbytes = len*2*(Py_ssize_t)sizeof(float);
  if(rowbytes <= 0 || b.len < rowbytes || b.len % rowbytes != 0){
    PyBuffer_Release(&b);
    return PyErr_Format(PyExc_ValueError,"buffer size must be a positive multiple of row size (%zd bytes)",rowbytes);
  }
  int count = (int)(b.len / rowbytes);
  int limit = is_data ? f.nd : f.nt;
  if(i0 < 0 || i0 + count > limit){
    PyBuffer_Release(&b);
    return PyErr_Format(PyExc_IndexError,"range [%d, %d) exceeds limit %d",i0,i0+count,limit);
  }
  const float *ptr = (const float*)b.buf;
  int r = 0;
  Py_BEGIN_ALLOW_THREADS
  for(int k=0;k<count;k++){
    r = set_spectrum(&f,is_data,i0+k,ptr+(size_t)k*len*2);
    if(r < 0) break;
  }
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b);
  if(r<0) return PyErr_Format(PyExc_RuntimeError,"failed setting spectrum at index %d",r);
  Py_RETURN_NONE;
}

/* The outputs of run and run_series: int64 bin indices, complex64 values, float32
   magnitudes (an empty buffer for none), int32 crossing counts per row, and the optional
   structured peaks (no buffer when absent). Callers zero only the optional buffers: zeroing
   all five compiled to a rep stos that made a one-bin run at n = 256 4% slower (23 ns a
   call, Zen 5). */
typedef struct { Py_buffer idx,val,mag,cnt,pk; } peak_out;
static void out_release(peak_out *o){
  PyBuffer_Release(&o->idx);PyBuffer_Release(&o->val);
  PyBuffer_Release(&o->mag);PyBuffer_Release(&o->cnt);
  if(o->pk.buf) PyBuffer_Release(&o->pk);
}
/* Copy a run's need peaks into the structured peaks, and into the index, value and
   magnitude arrays, where each is given and has room. */
static void out_copy(const peak_out *o,const ap_peak *pk,Py_ssize_t need){
  if(o->pk.buf && o->pk.len>=need*(Py_ssize_t)sizeof(ap_structured_peak)){
    ap_structured_peak *s=(ap_structured_peak*)o->pk.buf;
    for(Py_ssize_t a=0;a<need;a++){
      s[a].index=(int64_t)pk[a].index;
      s[a].re=pk[a].re;
      s[a].im=pk[a].im;
    }
  }
  if(o->idx.buf && o->idx.len>=need*8 && o->val.buf && o->val.len>=need*8){
    long long *ix=(long long*)o->idx.buf; float *vl=(float*)o->val.buf,*mg=o->mag.len ? (float*)o->mag.buf : NULL;
    for(Py_ssize_t a=0;a<need;a++){
      ix[a]=(long long)pk[a].index; vl[2*a]=pk[a].re; vl[2*a+1]=pk[a].im; if(mg) mg[a]=pk[a].magnitude;
    }
  }
}

/* run(d0,nd,t0,nt,binsize,threshold,start,end, idx,val,mag,counts [, peaks]) -> total */
static PyObject *bind_run(filter_view f,PyObject *args){
  int d0,nd,t0,nt; Py_ssize_t binsize,start,end; double thr;
  peak_out o; o.pk=(Py_buffer){0};
  if(!PyArg_ParseTuple(args,"iiiindnnw*w*w*w*|w*",&d0,&nd,&t0,&nt,&binsize,&thr,
                       &start,&end,&o.idx,&o.val,&o.mag,&o.cnt,&o.pk)) return NULL;
  size_t nb; Py_ssize_t rows,need; ap_peak *pk=NULL;
  if(!run_shape(f.n,f.nd,f.nt,d0,nd,t0,nt,binsize,start,end,&nb,&rows)
     || !output_shape(rows,nb,&o.idx,&o.val,&o.mag,&o.cnt,&o.pk,&need)
     || !(pk=reserve_peaks(f.peaks,f.capacity,need))){
    out_release(&o);
    return NULL;
  }
  int tot;
  Py_BEGIN_ALLOW_THREADS
  if(f.hier) tot=ap_hmf_run(f.p,d0,nd,t0,nt,(size_t)binsize,(float)thr,pk,(int*)o.cnt.buf,
                            (size_t)start,(size_t)end);
  else tot=ap_mf_run(f.p,d0,nd,t0,nt,(size_t)binsize,(float)thr,pk,(int*)o.cnt.buf,
                     (size_t)start,(size_t)end);
  Py_END_ALLOW_THREADS
  if(tot>=0) out_copy(&o,pk,need);
  out_release(&o);
  if(tot<0){ PyErr_SetString(PyExc_RuntimeError,f.hier ? "matchedfilter: hierarchical filter failed"
                                                       : "matchedfilter: matched filter failed");
             return NULL; }
  return PyLong_FromLong(tot);
}

/* The samples in a series buffer of len bytes: complex64, or float32 real samples
   stride floats apart (HMF set_real_series). */
static size_t series_samples(Py_ssize_t len,int real,int stride){
  return real ? ((size_t)(len/4)+(size_t)stride-1)/(size_t)(stride?stride:1) : (size_t)(len/8);
}
/* The optional structured peaks argument: None (or absent) for none. Returns 1, or 0 with
   the exception set when it is not a writable buffer. */
static int peaks_arg(PyObject *o,Py_buffer *pk){
  return !o || o==Py_None || PyObject_GetBuffer(o,pk,PyBUF_WRITABLE)==0;
}
/* The buffers of a run_series call: the series, its block layout (starts, window starts,
   window ends), the bin phases (no buffer when absent) and the outputs. */
typedef struct { Py_buffer s,st,ws,we,ph; peak_out o; } series_bufs;
static void series_release(series_bufs *c){
  PyBuffer_Release(&c->s);PyBuffer_Release(&c->st);
  PyBuffer_Release(&c->ws);PyBuffer_Release(&c->we);
  out_release(&c->o);
  phase_release(&c->ph);
}
/* run_series(series, starts, wstart, wend, t0, nt, binsize, thr, idx,val,mag,cnt
   [, peaks or None [, bin_phase: uint32 per block, or None]]) -> total, and with dif
   (MF only) run_series_dif(the same, but [, peaks or None, decimated [, bin_phase]]). */
static PyObject *bind_run_series(filter_view f,PyObject *args,int dif){
  series_bufs c; c.ph=(Py_buffer){0}; c.o.pk=(Py_buffer){0};
  int t0,nt,decimated=0; Py_ssize_t binsize; double thr;
  PyObject *pk_arg=NULL,*ph_arg=NULL;
  if(dif ? !PyArg_ParseTuple(args,"y*y*y*y*iindw*w*w*w*|OiO",&c.s,&c.st,&c.ws,&c.we,
                             &t0,&nt,&binsize,&thr,&c.o.idx,&c.o.val,&c.o.mag,&c.o.cnt,
                             &pk_arg,&decimated,&ph_arg)
         : !PyArg_ParseTuple(args,"y*y*y*y*iindw*w*w*w*|OO",&c.s,&c.st,&c.ws,&c.we,
                             &t0,&nt,&binsize,&thr,&c.o.idx,&c.o.val,&c.o.mag,&c.o.cnt,
                             &pk_arg,&ph_arg)) return NULL;
  /* run_series_dif takes the bin phases before the peaks: which error a call with both
     invalid raises. */
  int ok = dif ? phase_arg(ph_arg,&c.ph) && peaks_arg(pk_arg,&c.o.pk)
               : peaks_arg(pk_arg,&c.o.pk) && phase_arg(ph_arg,&c.ph);
  int nblocks=0; size_t nb=0;
  Py_ssize_t rows=0,need=0;
  ap_peak *pk=NULL;
  ok = ok && (dif ? series_shape_dif(f.n,f.nt,t0,nt,binsize,decimated,&c.s,&c.st,&c.ws,&c.we,
                                     &c.ph,&nblocks,&nb,&rows)
                  : series_shape_r(f.n,f.nt,t0,nt,binsize,f.real,&c.s,&c.st,&c.ws,&c.we,
                                   &c.ph,&nblocks,&nb,&rows))
     && output_shape(rows,nb,&c.o.idx,&c.o.val,&c.o.mag,&c.o.cnt,&c.o.pk,&need)
     && (pk=reserve_peaks(f.peaks,f.capacity,need));
  if(!ok){ series_release(&c); return NULL; }
  const size_t nseries=series_samples(c.s.len,f.real,f.real_stride);
  const float *ser=(const float*)c.s.buf;
  const size_t *st=(const size_t*)c.st.buf,*ws=(const size_t*)c.ws.buf,*we=(const size_t*)c.we.buf;
  const unsigned *ph=phase_of(&c.ph);
  int *cnt=(int*)c.o.cnt.buf;
  int tot;
  Py_BEGIN_ALLOW_THREADS
  if(dif) tot=ap_mf_run_series_dif(f.p,ser,nseries,st,ws,we,ph,nblocks,t0,nt,(size_t)binsize,
                                   (float)thr,decimated,pk,cnt);
  else if(f.hier) tot=ap_hmf_run_series(f.p,ser,nseries,st,ws,we,ph,nblocks,t0,nt,
                                        (size_t)binsize,(float)thr,pk,cnt);
  else tot=ap_mf_run_series(f.p,ser,nseries,st,ws,we,ph,nblocks,t0,nt,(size_t)binsize,
                            (float)thr,pk,cnt);
  Py_END_ALLOW_THREADS
  if(tot>=0) out_copy(&c.o,pk,need);
  series_release(&c);
  if(tot<0){ PyErr_SetString(PyExc_RuntimeError,dif ? "matchedfilter: run_series_dif failed"
                                                     : "matchedfilter: run_series failed");
             return NULL; }
  return PyLong_FromLong(tot);
}

/* ---------------- matched filter ---------------- */
typedef struct { PyObject_HEAD ap_mf_plan *p; Py_ssize_t n; int nd,nt; ap_peak *peaks; Py_ssize_t peak_capacity;
                 int busy; /* a method is running (GUARDED) */ } MFObject;

/* One filter object per thread. Methods release the GIL while the kernels run, and a
   plan's buffers are not safe for two calls at once: a second thread calling into the
   same object would corrupt them. GUARDED wraps a method so that a call while another is
   in flight raises instead; the flag is read and set with the GIL held, so the check
   itself cannot race. */
#define GUARDED(T,f) \
  static PyObject *f##_g(T *self,PyObject *args){ \
    if(self->busy){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter in use by " \
                                    "another thread; use one filter per thread"); return NULL; } \
    self->busy=1; PyObject *r=f(self,args); self->busy=0; return r; }
#define BUSY_GETTER(T) \
  static PyObject *T##_get_busy(T *self,void *closure){ (void)closure; return PyBool_FromLong(self->busy); }

static int MF_init(MFObject *self,PyObject *args,PyObject *kw){
  if(self->p){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter already initialised"); return -1; }
  Py_ssize_t n; int nd,nt; (void)kw;
  if(!PyArg_ParseTuple(args,"nii",&n,&nd,&nt)) return -1;
  self->p=ap_mf_create((size_t)n,nd,nt);
  if(!self->p){ PyErr_Format(PyExc_ValueError,
      "unsupported matched-filter shape n=%zd ndata=%d ntemplates=%d",n,nd,nt); return -1; }
  self->n=n; self->nd=nd; self->nt=nt; return 0;
}
static void MF_dealloc(MFObject *self){
  if(self->p) ap_mf_destroy(self->p);
  PyMem_Free(self->peaks);
  Py_TYPE(self)->tp_free((PyObject*)self);
}
static filter_view mf_view(MFObject *s){
  return (filter_view){s->p,0,s->n,s->n,s->nd,s->nt,&s->peaks,&s->peak_capacity,0,1};
}
static PyObject *MF_set_data(MFObject *s,PyObject *a){ return bind_set(mf_view(s),a,1); }
static PyObject *MF_set_template(MFObject *s,PyObject *a){ return bind_set(mf_view(s),a,0); }
static PyObject *MF_set_data_batch(MFObject *s,PyObject *a){ return bind_set_batch(mf_view(s),a,1); }
static PyObject *MF_set_template_batch(MFObject *s,PyObject *a){ return bind_set_batch(mf_view(s),a,0); }
static PyObject *MF_run(MFObject *s,PyObject *a){ return bind_run(mf_view(s),a); }
static PyObject *MF_run_series(MFObject *s,PyObject *a){ return bind_run_series(mf_view(s),a,0); }
static PyObject *MF_run_series_dif(MFObject *s,PyObject *a){ return bind_run_series(mf_view(s),a,1); }
/* q15_screen(d0, nd, t0, nt, threshold, start, end, pass[u8 nd*nt], stat[f32 nd*nt] or b"")
   -> pairs passed, or -1 when this plan has no Q15 screen (see ap_mf_q15_screen). */
static PyObject *MF_q15_screen(MFObject *self,PyObject *args){
  int d0,nd,t0,nt; double thr; Py_ssize_t start,end; Py_buffer bp,bs;
  if(!PyArg_ParseTuple(args,"iiiidnnw*w*",&d0,&nd,&t0,&nt,&thr,&start,&end,&bp,&bs)) return NULL;
  if(nd<1||nt<1||!ap_range_ok(d0,nd,self->nd)||!ap_range_ok(t0,nt,self->nt)||start<0||end<=start
     ||bp.len<(Py_ssize_t)nd*nt||(bs.len && bs.len<(Py_ssize_t)nd*nt*(Py_ssize_t)sizeof(float))){
    PyBuffer_Release(&bp);PyBuffer_Release(&bs);
    PyErr_SetString(PyExc_ValueError,"invalid q15_screen arguments"); return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_mf_q15_screen(self->p,d0,nd,t0,nt,(float)thr,(size_t)start,(size_t)end,
                     (unsigned char*)bp.buf,bs.len?(float*)bs.buf:NULL);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&bp);PyBuffer_Release(&bs);
  return PyLong_FromLong(r);
}
static PyObject *MF_q15_lanes(MFObject *self,PyObject *unused){
  (void)unused; return PyLong_FromLong(ap_mf_q15_lanes(self->p));
}
static PyObject *MF_correlate(MFObject *self,PyObject *args){
  int d0,nd,t0,nt; Py_buffer out;
  if(!PyArg_ParseTuple(args,"iiiiw*",&d0,&nd,&t0,&nt,&out)) return NULL;
  int valid=d0>=0&&nd>0&&nd<=self->nd&&d0<=self->nd-nd
    &&t0>=0&&nt>0&&nt<=self->nt&&t0<=self->nt-nt
    &&(size_t)nd<=SIZE_MAX/(size_t)nt
    &&(size_t)nd*(size_t)nt<=SIZE_MAX/((size_t)self->n*8)
    &&(size_t)out.len>=((size_t)nd*(size_t)nt*(size_t)self->n*8);
  if(!valid){ PyBuffer_Release(&out);
    PyErr_SetString(PyExc_ValueError,"invalid correlation output shape or subrange"); return NULL; }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_mf_correlate(self->p,d0,nd,t0,nt,(float*)out.buf);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&out);
  if(r){ PyErr_SetString(PyExc_RuntimeError,"correlation failed"); return NULL; }
  Py_RETURN_NONE;
}
static PyObject *MF_correlate_series(MFObject *self,PyObject *args){
  Py_buffer ser,starts,out;
  int t0,nt;
  if(!PyArg_ParseTuple(args,"y*y*iiw*",&ser,&starts,&t0,&nt,&out)) return NULL;
  const size_t rowbytes=(size_t)self->n*8;
  int valid=ser.len%8==0 && starts.len%sizeof(size_t)==0
    && starts.len/sizeof(size_t)>0 && starts.len/sizeof(size_t)<=INT_MAX
    && t0>=0 && nt>0 && nt<=self->nt && t0<=self->nt-nt;
  size_t blocks=(size_t)starts.len/sizeof(size_t);
  if(valid){
    valid=blocks<=SIZE_MAX/(size_t)nt
      && blocks*(size_t)nt<=SIZE_MAX/rowbytes
      && (size_t)out.len>=blocks*(size_t)nt*rowbytes;
  }
  if(valid){
    const size_t *st=(const size_t*)starts.buf;
    for(size_t i=0;i<blocks;i++) if(st[i]>SIZE_MAX-(size_t)self->n){valid=0;break;}
  }
  if(!valid){
    PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
    PyErr_SetString(PyExc_ValueError,"invalid series, starts, templates or full output shape");
    return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_mf_correlate_series(self->p,(const float*)ser.buf,(size_t)ser.len/8,
                           (const size_t*)starts.buf,(int)blocks,t0,nt,(float*)out.buf);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
  if(r){ PyErr_SetString(PyExc_RuntimeError,"full series correlation failed");return NULL; }
  Py_RETURN_NONE;
}
static PyObject *MF_correlate_series_continuous(MFObject *self,PyObject *args){
  Py_buffer ser,starts,out,bnd={0};
  Py_ssize_t lo,hi;
  int t0,nt;
  PyObject *bobj=Py_None;
  if(!PyArg_ParseTuple(args,"y*y*nniiw*|O",&ser,&starts,&lo,&hi,&t0,&nt,&out,&bobj)) return NULL;
  if(bobj!=Py_None && PyObject_GetBuffer(bobj,&bnd,PyBUF_SIMPLE)){
    PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);return NULL;
  }
  size_t blocks=(size_t)starts.len/sizeof(size_t);
  int valid=ser.len%8==0 && starts.len%sizeof(size_t)==0
    && blocks>0 && blocks<=INT_MAX && lo>=0 && lo<hi && hi<=self->n
    && t0>=0 && nt>0 && nt<=self->nt && t0<=self->nt-nt
    && ser.len<=PY_SSIZE_T_MAX/nt
    && (size_t)out.len==(size_t)nt*(size_t)ser.len;
  if(valid){
    const size_t *st=(const size_t*)starts.buf;
    for(size_t i=0;i<blocks;i++) if(st[i]>SIZE_MAX-(size_t)self->n){valid=0;break;}
  }
  /* bounds: one [lo, hi) per block inside [lo, hi), checked again by the kernel */
  if(valid && bnd.buf && (size_t)bnd.len!=2*blocks*sizeof(size_t)) valid=0;
  if(!valid){
    PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
    if(bnd.buf) PyBuffer_Release(&bnd);
    PyErr_SetString(PyExc_ValueError,"invalid continuous series output or block layout");
    return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_mf_correlate_series_continuous(self->p,(const float*)ser.buf,
                                      (size_t)ser.len/8,(const size_t*)starts.buf,
                                      (int)blocks,(size_t)lo,(size_t)hi,t0,nt,
                                      (float*)out.buf,(const size_t*)bnd.buf);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
  if(bnd.buf) PyBuffer_Release(&bnd);
  if(r){PyErr_SetString(PyExc_RuntimeError,"continuous series correlation failed");return NULL;}
  Py_RETURN_NONE;
}
/* correlate_series_continuous_real(series float32, starts, lo, hi, t0, nt, out complex64):
   correlate_series_continuous of a real series, at half-size block transforms. */
static PyObject *MF_correlate_series_continuous_real(MFObject *self,PyObject *args){
  Py_buffer ser,starts,out,bnd={0};
  Py_ssize_t lo,hi;
  int t0,nt;
  PyObject *bobj=Py_None;
  if(!PyArg_ParseTuple(args,"y*y*nniiw*|O",&ser,&starts,&lo,&hi,&t0,&nt,&out,&bobj)) return NULL;
  if(bobj!=Py_None && PyObject_GetBuffer(bobj,&bnd,PyBUF_SIMPLE)){
    PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);return NULL;
  }
  size_t blocks=(size_t)starts.len/sizeof(size_t);
  const size_t nseries=(size_t)ser.len/4;
  int valid=ser.len%4==0 && starts.len%sizeof(size_t)==0
    && blocks>0 && blocks<=INT_MAX && lo>=0 && lo<hi && hi<=self->n
    && t0>=0 && nt>0 && nt<=self->nt && t0<=self->nt-nt
    && nseries<=(size_t)PY_SSIZE_T_MAX/8/(size_t)nt
    && (size_t)out.len==(size_t)nt*nseries*8;
  if(valid){
    const size_t *st=(const size_t*)starts.buf;
    for(size_t i=0;i<blocks;i++) if(st[i]>SIZE_MAX-(size_t)self->n){valid=0;break;}
  }
  /* bounds: one [lo, hi) per block inside [lo, hi), checked again by the kernel */
  if(valid && bnd.buf && (size_t)bnd.len!=2*blocks*sizeof(size_t)) valid=0;
  if(!valid){
    PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
    if(bnd.buf) PyBuffer_Release(&bnd);
    PyErr_SetString(PyExc_ValueError,"invalid real continuous series output or block layout");
    return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_mf_correlate_series_continuous_real(self->p,(const float*)ser.buf,nseries,
                                           (const size_t*)starts.buf,(int)blocks,
                                           (size_t)lo,(size_t)hi,t0,nt,(float*)out.buf,(const size_t*)bnd.buf);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&ser);PyBuffer_Release(&starts);PyBuffer_Release(&out);
  if(bnd.buf) PyBuffer_Release(&bnd);
  if(r){PyErr_SetString(PyExc_RuntimeError,"real continuous series correlation failed");return NULL;}
  Py_RETURN_NONE;
}
static PyObject *MF_nbins(MFObject *self,PyObject *args){
  Py_ssize_t bs,st,en;
  if(!PyArg_ParseTuple(args,"nnn",&bs,&st,&en)) return NULL;
  return PyLong_FromSize_t(ap_mf_nbins(self->p,(size_t)bs,(size_t)st,(size_t)en));
}
GUARDED(MFObject,MF_set_data)
GUARDED(MFObject,MF_correlate_series_continuous_real)
GUARDED(MFObject,MF_set_template)
GUARDED(MFObject,MF_set_data_batch)
GUARDED(MFObject,MF_set_template_batch)
GUARDED(MFObject,MF_run)
GUARDED(MFObject,MF_correlate)
GUARDED(MFObject,MF_correlate_series)
GUARDED(MFObject,MF_correlate_series_continuous)
GUARDED(MFObject,MF_run_series)
GUARDED(MFObject,MF_run_series_dif)
GUARDED(MFObject,MF_nbins)
GUARDED(MFObject,MF_q15_screen)
GUARDED(MFObject,MF_q15_lanes)
static PyMethodDef MF_methods[]={
  {"set_data",(PyCFunction)MF_set_data_g,METH_VARARGS,"set_data(i, buffer)"},
  {"correlate_series_continuous_real",(PyCFunction)MF_correlate_series_continuous_real_g,METH_VARARGS,"correlate_series_continuous_real(series_f32, starts, lo, hi, t0, nt, out_c64): the same of a real series, half-size block transforms"},
  {"set_template",(PyCFunction)MF_set_template_g,METH_VARARGS,"set_template(i, buffer)"},
  {"set_data_batch",(PyCFunction)MF_set_data_batch_g,METH_VARARGS,"set_data_batch(i0, buffer)"},
  {"set_template_batch",(PyCFunction)MF_set_template_batch_g,METH_VARARGS,"set_template_batch(i0, buffer)"},
  {"run",(PyCFunction)MF_run_g,METH_VARARGS,"run(...) -> total crossings"},
  {"correlate",(PyCFunction)MF_correlate_g,METH_VARARGS,"correlate(...) -> full correlation"},
  {"correlate_series",(PyCFunction)MF_correlate_series_g,METH_VARARGS,"correlate_series(...) -> full correlation"},
  {"correlate_series_continuous",(PyCFunction)MF_correlate_series_continuous_g,METH_VARARGS,
   "correlate_series_continuous(...) -> continuous valid correlation"},
  {"run_series",(PyCFunction)MF_run_series_g,METH_VARARGS,"run_series(...)"},
  {"run_series_dif",(PyCFunction)MF_run_series_dif_g,METH_VARARGS,"run_series_dif(...)"},
  {"nbins",(PyCFunction)MF_nbins_g,METH_VARARGS,"nbins(binsize, start, end)"},
  {"q15_screen",(PyCFunction)MF_q15_screen_g,METH_VARARGS,"q15_screen(d0,nd,t0,nt,thr,start,end,pass,stat) -> passed"},
  {"q15_lanes",(PyCFunction)MF_q15_lanes_g,METH_NOARGS,"q15_lanes() -> pairs per Q15 screen call, 0 if none"},
  {NULL}
};
BUSY_GETTER(MFObject)
static PyGetSetDef MF_getset[] = {
  {"_busy", (getter)MFObject_get_busy, NULL, "a method is running on this object", NULL},
  {NULL}
};
static PyTypeObject MFType={
  PyVarObject_HEAD_INIT(NULL,0)
  .tp_name="matchedfilter._core.MF", .tp_basicsize=sizeof(MFObject),
  .tp_flags=Py_TPFLAGS_DEFAULT, .tp_new=PyType_GenericNew,
  .tp_init=(initproc)MF_init, .tp_dealloc=(destructor)MF_dealloc,
  .tp_methods=MF_methods, .tp_getset=MF_getset, .tp_doc="matchedfilter matched filter (opaque)",
};

/* ---------------- hierarchical matched filter ---------------- */
/* Same shape as MF, so the Python class can share almost all of its code.  The
   only genuinely new surface is stats(), which reports the trigger rate - the
   quantity the whole speedup rides on, and the first thing to look at when the
   filter is slower than expected on a particular data set. */
typedef struct { PyObject_HEAD ap_hmf_plan *p; Py_ssize_t n, k; int nd,nt; ap_peak *peaks; Py_ssize_t peak_capacity;
                 int real; /* run_series reads a real series (set_real_series) */
                 int real_stride; /* floats between its samples: 1, or 2 for a complex lane */
                 int busy; /* a method is running (GUARDED) */
                 PyObject *owner; /* the HMF whose template storage this one reads (share=), kept alive */ } HMFObject;

/* HMF(n, ndata, ntemplates, bands, series_group=8, k=0, share=None): a gate chain of coarse
   bands (strictly increasing), then the full refine. Thresholds come from Python. share:
   another HMF of the same templates (same n, k, ntemplates, data rows), whose
   full-resolution templates and taps this one reads instead of holding copies. */
static int HMF_init(HMFObject *self,PyObject *args,PyObject *kw){
  if(self->p){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter already initialised"); return -1; }
  Py_ssize_t n; int nd,nt; PyObject *bands_obj; (void)kw;
  int group=8; Py_ssize_t k_bins=0; PyObject *share=Py_None;
  if(!PyArg_ParseTuple(args,"niiO|inO",&n,&nd,&nt,&bands_obj,&group,&k_bins,&share)) return -1;
  if(share!=Py_None && (Py_TYPE(share)!=Py_TYPE(self) || !((HMFObject*)share)->p
                        || ((HMFObject*)share)->owner)){
    PyErr_SetString(PyExc_TypeError,"share must be an HMF that holds its own templates"); return -1; }
  PyObject *seq=PySequence_Fast(bands_obj,"bands must be a sequence of ints");
  if(!seq) return -1;
  Py_ssize_t nti=PySequence_Fast_GET_SIZE(seq);
  if(nti<1 || nti>AP_HMF_MAX_TIERS){ Py_DECREF(seq);
    PyErr_Format(PyExc_ValueError,"a chain has 1..%d bands",AP_HMF_MAX_TIERS); return -1; }
  size_t bands[AP_HMF_MAX_TIERS];
  for(Py_ssize_t i=0;i<nti;i++){
    Py_ssize_t v=PyNumber_AsSsize_t(PySequence_Fast_GET_ITEM(seq,i),PyExc_OverflowError);
    if(v==-1 && PyErr_Occurred()){ Py_DECREF(seq); return -1; }
    bands[i]=(size_t)v;
  }
  Py_DECREF(seq);
  self->k = (k_bins > 0) ? k_bins : n;
  self->p = share!=Py_None
    ? ap_hmf_create_chain_shared(((HMFObject*)share)->p,(size_t)n,(size_t)self->k,nd,nt,bands,(int)nti,group)
    : ap_hmf_create_chain((size_t)n,(size_t)self->k,nd,nt,bands,(int)nti,group);
  if(self->p && share!=Py_None){ Py_INCREF(share); self->owner=share; }
  if(!self->p){ PyErr_Format(PyExc_ValueError,
      "no hierarchical plan for n=%zd k=%zd with this chain (bands must be supported "
      "powers of two, strictly increasing and < n)",n,self->k); return -1; }
  self->n=n; self->nd=nd; self->nt=nt; return 0;
}
static void HMF_dealloc(HMFObject *self){
  if(self->p) ap_hmf_destroy(self->p);
  Py_XDECREF(self->owner);
  PyMem_Free(self->peaks);
  Py_TYPE(self)->tp_free((PyObject*)self);
}
static filter_view hmf_view(HMFObject *s){
  return (filter_view){s->p,1,s->n,s->k,s->nd,s->nt,&s->peaks,&s->peak_capacity,s->real,
                       s->real_stride};
}
static PyObject *HMF_set_reference(HMFObject *self,PyObject *args){
  Py_buffer b;
  if(!PyArg_ParseTuple(args,"z*",&b)) return NULL;
  int r;
  if(!b.buf){ r=ap_hmf_set_reference(self->p,NULL); }
  else {
    if(b.len < self->k*(Py_ssize_t)sizeof(float)){
      PyBuffer_Release(&b);
      return PyErr_Format(PyExc_ValueError,
                          "reference must hold %zd float32 values",self->k);
    }
    r=ap_hmf_set_reference(self->p,(const float*)b.buf);
  }
  PyBuffer_Release(&b);
  if(r<0){ PyErr_SetString(PyExc_ValueError,"matchedfilter: bad reference"); return NULL; }
  Py_RETURN_NONE;
}
static PyObject *HMF_set_data(HMFObject *s,PyObject *a){ return bind_set(hmf_view(s),a,1); }
static PyObject *HMF_set_template(HMFObject *s,PyObject *a){ return bind_set(hmf_view(s),a,0); }
static PyObject *HMF_set_data_batch(HMFObject *s,PyObject *a){ return bind_set_batch(hmf_view(s),a,1); }
static PyObject *HMF_set_template_batch(HMFObject *s,PyObject *a){ return bind_set_batch(hmf_view(s),a,0); }
static PyObject *HMF_run(HMFObject *s,PyObject *a){ return bind_run(hmf_view(s),a); }
static PyObject *HMF_run_series(HMFObject *s,PyObject *a){ return bind_run_series(hmf_view(s),a,0); }
#include "hmf.h"
static PyTypeObject HMFType;
static int cnt_arg(PyObject *o,Py_ssize_t rows,Py_buffer *bcnt){
  bcnt->buf=NULL;
  if(!o || o==Py_None) return 1;
  if(PyObject_GetBuffer(o,bcnt,PyBUF_WRITABLE)<0) return 0;
  if(bcnt->len/(Py_ssize_t)sizeof(int)<rows){
    PyBuffer_Release(bcnt); bcnt->buf=NULL;
    PyErr_SetString(PyExc_ValueError,"counts buffer too small");
    return 0;
  }
  return 1;
}
static void cnt_release(Py_buffer *bcnt){
  if(bcnt->buf){ PyBuffer_Release(bcnt); bcnt->buf=NULL; }
}
static PyObject *sparse_job_tuple(const ap_hmf_sparse_job *jb){
  const Py_ssize_t m=(Py_ssize_t)jb->out_count;
  if(m<0 || m>PY_SSIZE_T_MAX/8){
    PyErr_SetString(PyExc_RuntimeError,"inconsistent sparse peak count");
    return NULL;
  }
  PyObject *fl=PyBytes_FromStringAndSize(NULL,m*8),
           *ix=PyBytes_FromStringAndSize(NULL,m*8),
           *vl=PyBytes_FromStringAndSize(NULL,m*8);
  if(!fl||!ix||!vl){ Py_XDECREF(fl); Py_XDECREF(ix); Py_XDECREF(vl); return NULL; }
  if(m){
    memcpy(PyBytes_AS_STRING(fl),jb->out_flat,(size_t)m*8u);
    memcpy(PyBytes_AS_STRING(ix),jb->out_idx,(size_t)m*8u);
    memcpy(PyBytes_AS_STRING(vl),jb->out_val,(size_t)m*8u);
  }
  return Py_BuildValue("(NNNi)",fl,ix,vl,jb->total);
}
/* run_series_sparse(series, starts, wstart, wend, t0, nt, binsize, thr, cnt[i32 rows]|None)
   -> (flat, index, value, total): int64 flat positions in the (blocks, nt, bins) table,
   int64 bin indices and complex64 values of every peak, in C order. */
static PyObject *HMF_run_series_sparse(HMFObject *self,PyObject *args){
  Py_buffer bs,bst,bws,bwe,bcnt={0},bph={0};
  int t0,nt; Py_ssize_t binsize; double thr;
  PyObject *cnt_obj=NULL,*ph_arg=NULL;
  if(!PyArg_ParseTuple(args,"y*y*y*y*iindO|O",&bs,&bst,&bws,&bwe,&t0,&nt,&binsize,&thr,&cnt_obj,
                       &ph_arg))
    return NULL;
  int nblocks; size_t nb; Py_ssize_t rows;
  PyObject *ret=NULL;
  ap_hmf_sparse_job jb={0};
  if(!phase_arg(ph_arg,&bph)) goto done;
  if(!series_shape_r(self->n,self->nt,t0,nt,binsize,self->real,&bs,&bst,&bws,&bwe,&bph,
                     &nblocks,&nb,&rows))
    goto done;
  if(!cnt_arg(cnt_obj,rows,&bcnt)) goto done;
  if(nb>(size_t)PY_SSIZE_T_MAX/(size_t)rows
     || rows*(Py_ssize_t)nb>PY_SSIZE_T_MAX/(Py_ssize_t)sizeof(ap_peak)){
    PyErr_SetString(PyExc_ValueError,"overflowing output shape"); goto done; }
  jb.p=self->p;
  jb.series=(const float*)bs.buf;
  jb.nseries=series_samples(bs.len,self->real,self->real_stride);
  jb.start=(const size_t*)bst.buf;
  jb.win_start=(const size_t*)bws.buf;
  jb.win_end=(const size_t*)bwe.buf;
  jb.bin_phase=phase_of(&bph);
  jb.nblocks=nblocks; jb.t0=t0; jb.nt=nt;
  jb.binsize=(size_t)binsize; jb.threshold=(float)thr;
  jb.counts=(int*)bcnt.buf; jb.cluster_id=0;
  int rc;
  Py_BEGIN_ALLOW_THREADS
  rc=ap_hmf_run_series_batch_sparse(&jb,1);
  Py_END_ALLOW_THREADS
  if(rc<0){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done; }
  ret=sparse_job_tuple(&jb);
done:
  free(jb.out_flat); free(jb.out_idx); free(jb.out_val);
  PyBuffer_Release(&bs);PyBuffer_Release(&bst);PyBuffer_Release(&bws);PyBuffer_Release(&bwe);
  cnt_release(&bcnt);
  phase_release(&bph);
  return ret;
}
typedef struct {
  Py_buffer bs,bst,bws,bwe,bcnt,bph;
  int have_main;
  HMFObject *hmf;
} hmf_batch_item;
static PyObject *HMF_run_series_batch_sparse(PyObject *cls_unused,PyObject *seq_arg){
  (void)cls_unused;
  PyObject *seq=PySequence_Fast(seq_arg,"jobs must be a sequence");
  if(!seq) return NULL;
  const Py_ssize_t n=PySequence_Fast_GET_SIZE(seq);
  if(n==0){ Py_DECREF(seq); return PyList_New(0); }
  if(n>INT_MAX){ Py_DECREF(seq); PyErr_SetString(PyExc_ValueError,"too many batch jobs"); return NULL; }
  hmf_batch_item *items=PyMem_Calloc((size_t)n,sizeof(*items));
  ap_hmf_sparse_job *jobs=PyMem_Calloc((size_t)n,sizeof(*jobs));
  PyObject *out=NULL;
  if(!items||!jobs){ PyErr_NoMemory(); goto done; }
  for(Py_ssize_t i=0;i<n;i++){
    PyObject *it=PySequence_Fast_GET_ITEM(seq,i);
    hmf_batch_item *bi=&items[i];
    int t0=0,nt=0,cluster_id=0; Py_ssize_t binsize=0; double thr=0.0;
    PyObject *cnt_obj=NULL,*ph_obj=NULL;
    if(!PyArg_ParseTuple(it,"O!y*y*y*y*iindOOi",&HMFType,&bi->hmf,&bi->bs,&bi->bst,&bi->bws,
                         &bi->bwe,&t0,&nt,&binsize,&thr,&cnt_obj,&ph_obj,&cluster_id))
      goto done;
    Py_INCREF(bi->hmf);
    bi->have_main=1;
    if(bi->hmf->busy){
      PyErr_SetString(PyExc_RuntimeError,
                      "matchedfilter: filter in use by another thread; use one filter per thread");
      goto done;
    }
    int nblocks=0; size_t nb=0; Py_ssize_t rows=0;
    if(!phase_arg(ph_obj,&bi->bph)) goto done;
    if(!series_shape_r(bi->hmf->n,bi->hmf->nt,t0,nt,binsize,bi->hmf->real,&bi->bs,&bi->bst,
                       &bi->bws,&bi->bwe,&bi->bph,&nblocks,&nb,&rows))
      goto done;
    if(!cnt_arg(cnt_obj,rows,&bi->bcnt)) goto done;
    if(nb>(size_t)PY_SSIZE_T_MAX/(size_t)rows
       || rows*(Py_ssize_t)nb>PY_SSIZE_T_MAX/(Py_ssize_t)sizeof(ap_peak)){
      PyErr_SetString(PyExc_ValueError,"overflowing output shape"); goto done;
    }
    ap_hmf_sparse_job *jb=&jobs[i];
    jb->p=bi->hmf->p;
    jb->series=(const float*)bi->bs.buf;
    jb->nseries=series_samples(bi->bs.len,bi->hmf->real,bi->hmf->real_stride);
    jb->start=(const size_t*)bi->bst.buf;
    jb->win_start=(const size_t*)bi->bws.buf;
    jb->win_end=(const size_t*)bi->bwe.buf;
    jb->bin_phase=phase_of(&bi->bph);
    jb->nblocks=nblocks; jb->t0=t0; jb->nt=nt;
    jb->binsize=(size_t)binsize; jb->threshold=(float)thr;
    jb->counts=(int*)bi->bcnt.buf; jb->cluster_id=cluster_id;
  }
  for(Py_ssize_t i=0;i<n;i++) items[i].hmf->busy=1;
  int rc;
  Py_BEGIN_ALLOW_THREADS
  rc=ap_hmf_run_series_batch_sparse(jobs,(int)n);
  Py_END_ALLOW_THREADS
  for(Py_ssize_t i=0;i<n;i++) items[i].hmf->busy=0;
  if(rc<0){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done; }
  out=PyList_New(n);
  if(!out) goto done;
  for(Py_ssize_t i=0;i<n;i++){
    PyObject *tup=sparse_job_tuple(&jobs[i]);
    if(!tup){ Py_CLEAR(out); goto done; }
    PyList_SET_ITEM(out,i,tup);
  }
done:
  if(jobs){
    for(Py_ssize_t i=0;i<n;i++){
      free(jobs[i].out_flat); free(jobs[i].out_idx); free(jobs[i].out_val);
    }
  }
  if(items){
    for(Py_ssize_t i=0;i<n;i++){
      if(items[i].have_main){
        PyBuffer_Release(&items[i].bs); PyBuffer_Release(&items[i].bst);
        PyBuffer_Release(&items[i].bws); PyBuffer_Release(&items[i].bwe);
      }
      cnt_release(&items[i].bcnt);
      phase_release(&items[i].bph);
      Py_XDECREF(items[i].hmf);
    }
  }
  PyMem_Free(jobs);
  PyMem_Free(items);
  Py_DECREF(seq);
  return out;
}
static PyObject *HMF_nbins(HMFObject *self,PyObject *args){
  Py_ssize_t bs,st,en;
  if(!PyArg_ParseTuple(args,"nnn",&bs,&st,&en)) return NULL;
  return PyLong_FromSize_t(ap_hmf_nbins(self->p,(size_t)bs,(size_t)st,(size_t)en));
}
static PyObject *HMF_stats(HMFObject *self,PyObject *a){
  long pr=0,tg=0; (void)a; ap_hmf_stats(self->p,&pr,&tg);
  return Py_BuildValue("(ll)",pr,tg);
}
static PyObject *HMF_chain(HMFObject *self,PyObject *a){
  size_t bands[AP_HMF_MAX_TIERS]; (void)a;
  int nti=ap_hmf_chain(self->p,bands);
  PyObject *t=PyTuple_New(nti);
  if(!t) return NULL;
  for(int i=0;i<nti;i++) PyTuple_SET_ITEM(t,i,PyLong_FromSize_t(bands[i]));
  return t;
}
static PyObject *HMF_band_offsets(HMFObject *self,PyObject *a){
  size_t k0s[AP_HMF_MAX_TIERS]; (void)a;
  int nti=ap_hmf_band_offsets(self->p,k0s);
  PyObject *t=PyTuple_New(nti);
  if(!t) return NULL;
  for(int i=0;i<nti;i++) PyTuple_SET_ITEM(t,i,PyLong_FromSize_t(k0s[i]));
  return t;
}
static PyObject *HMF_set_band_offsets(HMFObject *self,PyObject *args){
  PyObject *obj;
  if(!PyArg_ParseTuple(args,"O",&obj)) return NULL;
  PyObject *seq=PySequence_Fast(obj,"band_offsets must be a sequence");
  if(!seq) return NULL;
  Py_ssize_t m=PySequence_Fast_GET_SIZE(seq);
  size_t k0s[AP_HMF_MAX_TIERS];
  if(m<1 || m>AP_HMF_MAX_TIERS){
    Py_DECREF(seq); PyErr_SetString(PyExc_ValueError,"one band offset per tier"); return NULL;
  }
  for(Py_ssize_t i=0;i<m;i++){
    long long v=PyLong_AsLongLong(PySequence_Fast_GET_ITEM(seq,i));
    if(v==-1 && PyErr_Occurred()){ Py_DECREF(seq); return NULL; }
    if(v<0){
      Py_DECREF(seq); PyErr_SetString(PyExc_ValueError,"band offsets must be non-negative"); return NULL;
    }
    k0s[i]=(size_t)v;
  }
  Py_DECREF(seq);
  if(ap_hmf_set_band_offsets(self->p,k0s,(int)m)<0){
    PyErr_SetString(PyExc_ValueError,"set_band_offsets: need one valid k0 (< n/2) per tier"); return NULL;
  }
  Py_RETURN_NONE;
}
/* [(band, passed, ticks) per tier] + [(n, refined, ticks)] */
static PyObject *HMF_tier_stats(HMFObject *self,PyObject *a){
  size_t bands[AP_HMF_MAX_TIERS]; (void)a;
  int nti=ap_hmf_chain(self->p,bands);
  PyObject *l=PyList_New(nti+1);
  if(!l) return NULL;
  for(int i=0;i<=nti;i++){
    long passed=0; unsigned long long ticks=0;
    ap_hmf_tier_stats(self->p,i,&passed,&ticks);
    PyList_SET_ITEM(l,i,Py_BuildValue("(nlK)",(Py_ssize_t)(i<nti ? bands[i] : (size_t)self->n),passed,ticks));
  }
  return l;
}
static PyObject *HMF_tier_inputs(HMFObject *self,PyObject *unused){
  long checked[AP_HMF_MAX_TIERS]; (void)unused;
  const int n=ap_hmf_tier_inputs(self->p,checked);
  PyObject *out=PyTuple_New(n);
  if(!out) return NULL;
  for(int i=0;i<n;i++) PyTuple_SET_ITEM(out,i,PyLong_FromLong(checked[i]));
  return out;
}
static PyObject *HMF_series_ticks(HMFObject *self,PyObject *a){
  (void)a; return PyLong_FromUnsignedLongLong(ap_hmf_series_ticks(self->p));
}
static PyObject *HMF_thresholds(HMFObject *self,PyObject *a){
  float thr[AP_HMF_MAX_TIERS]; (void)a;
  int nti=ap_hmf_thresholds(self->p,thr);
  PyObject *t=PyTuple_New(nti);
  if(!t) return NULL;
  for(int i=0;i<nti;i++) PyTuple_SET_ITEM(t,i,PyFloat_FromDouble((double)thr[i]));
  return t;
}
static PyObject *HMF_set_thresholds(HMFObject *self,PyObject *args){
  PyObject *obj;
  if(!PyArg_ParseTuple(args,"O",&obj)) return NULL;
  PyObject *seq=PySequence_Fast(obj,"thresholds must be a sequence");
  if(!seq) return NULL;
  Py_ssize_t m=PySequence_Fast_GET_SIZE(seq);
  float thr[AP_HMF_MAX_TIERS];
  if(m<1 || m>AP_HMF_MAX_TIERS){ Py_DECREF(seq); PyErr_SetString(PyExc_ValueError,"one threshold per tier"); return NULL; }
  for(Py_ssize_t i=0;i<m;i++){
    double v=PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq,i));
    if(v==-1.0 && PyErr_Occurred()){ Py_DECREF(seq); return NULL; }
    thr[i]=(float)v;
  }
  Py_DECREF(seq);
  if(ap_hmf_set_thresholds(self->p,thr,(int)m)<0){
    PyErr_SetString(PyExc_ValueError,"set_thresholds: need one finite value per tier"); return NULL; }
  Py_RETURN_NONE;
}

/* set_taps(taps, stride, counts, complex=False): taps float32 or complex64 (nt, stride),
   counts int64 (nt,). */
static PyObject *HMF_set_taps(HMFObject *self,PyObject *args){
  Py_buffer bt,bc; Py_ssize_t stride; int cplx=0;
  if(!PyArg_ParseTuple(args,"y*ny*|p",&bt,&stride,&bc,&cplx)) return NULL;
  int r=-1;
  const Py_ssize_t elem=cplx ? 2*(Py_ssize_t)sizeof(float) : (Py_ssize_t)sizeof(float);
  if(stride>0 && buf_holds(bt.len,self->nt,stride,elem)
     && bc.len>=(Py_ssize_t)self->nt*(Py_ssize_t)sizeof(int64_t))
    r = cplx ? ap_hmf_set_taps_complex(self->p,(const float*)bt.buf,(size_t)stride,(const int64_t*)bc.buf)
             : ap_hmf_set_taps(self->p,(const float*)bt.buf,(size_t)stride,(const int64_t*)bc.buf);
  PyBuffer_Release(&bt); PyBuffer_Release(&bc);
  if(r<0){ PyErr_SetString(PyExc_ValueError,"matchedfilter: bad taps (need nt rows of float32 "
                           "or complex64 taps, int64 counts in [1, min(stride, n)])"); return NULL; }
  Py_RETURN_NONE;
}
/* set_real_series(on) -> True if run_series now reads real float32 series. */
static PyObject *HMF_set_real_series(HMFObject *self,PyObject *args){
  int on, stride=1;
  if(!PyArg_ParseTuple(args,"p|i",&on,&stride)) return NULL;
  if(stride<1||stride>2){ PyErr_SetString(PyExc_ValueError,"stride must be 1 or 2"); return NULL; }
  if(ap_hmf_set_real_series(self->p,on) || ap_hmf_set_real_stride(self->p,(size_t)stride))
    Py_RETURN_FALSE;
  self->real=on; self->real_stride=stride;
  Py_RETURN_TRUE;
}
static PyObject *HMF_set_direct(HMFObject *self,PyObject *args){
  int on,hw=1; if(!PyArg_ParseTuple(args,"p|i",&on,&hw)) return NULL;
  return PyBool_FromLong(ap_hmf_set_direct(self->p,on,hw)==0);
}
static PyObject *HMF_price_direct_pair(HMFObject *self,PyObject *unused){
  (void)unused; double lt=0,fp=0;
  if(ap_hmf_price_direct_pair(self->p,&lt,&fp)) Py_RETURN_NONE;
  return Py_BuildValue("(dd)",lt,fp);
}
static PyObject *HMF_set_direct_prices(HMFObject *self,PyObject *args){
  double lt,fp; if(!PyArg_ParseTuple(args,"dd",&lt,&fp)) return NULL;
  return PyBool_FromLong(ap_hmf_set_direct_prices(self->p,lt,fp)==0);
}
static PyObject *HMF_direct_stats(HMFObject *self,PyObject *unused){
  (void)unused; long pairs=0,lags=0,fft=0; double lt=0,fp=0;
  ap_hmf_direct_stats(self->p,&pairs,&lags,&fft,&lt,&fp);
  return Py_BuildValue("{s:l,s:l,s:l,s:d,s:d}","pairs",pairs,"lags",lags,"fft",fft,
                       "ticks_per_lag_tap",lt,"ticks_per_fft_pair",fp);
}
static PyObject *HMF_set_q15(HMFObject *self,PyObject *args){
  int on; if(!PyArg_ParseTuple(args,"p",&on)) return NULL;
  return PyBool_FromLong(ap_hmf_set_q15(self->p,on)==0);
}
static PyObject *HMF_q15_stats(HMFObject *self,PyObject *unused){
  (void)unused; long passed=0; unsigned long long ticks=0;
  ap_hmf_q15_stats(self->p,&passed,&ticks);
  return Py_BuildValue("(iLK)",ap_hmf_get_q15(self->p),(long long)passed,ticks);
}
static PyObject *HMF_series_group(HMFObject *self,PyObject *unused){
  (void)unused; return PyLong_FromLong(ap_hmf_series_group(self->p));
}

int ap_hmf_set_tier0_clusters(ap_hmf_plan *p,int nc,const float *specs,
                              const int *offsets,const int *members,int lag_pad);
void ap_hmf_clear_tier0_clusters(ap_hmf_plan *p);
int ap_hmf_tier0_cluster_count(const ap_hmf_plan *p);
int ap_hmf_set_tier1_clusters(ap_hmf_plan *p,int nc,const float *specs,
                              const int *offsets,const int *members,int lag_pad);
void ap_hmf_clear_tier1_clusters(ap_hmf_plan *p);
int ap_hmf_tier1_cluster_count(const ap_hmf_plan *p);

static PyObject *HMF_set_tier0_clusters(HMFObject *self,PyObject *args){
  Py_buffer bsp,boff,bmem;
  int lag_pad=0;
  if(!PyArg_ParseTuple(args,"y*y*y*|i",&bsp,&boff,&bmem,&lag_pad)) return NULL;
  size_t bands[AP_HMF_MAX_TIERS];
  int nti=ap_hmf_chain(self->p,bands);
  int valid = boff.len%(Py_ssize_t)sizeof(int)==0
    && boff.len>=2*(Py_ssize_t)sizeof(int)
    && bmem.len==(Py_ssize_t)self->nt*(Py_ssize_t)sizeof(int);
  int nc = valid ? (int)(boff.len/(Py_ssize_t)sizeof(int))-1 : 0;
  if(valid){
    valid = nti>=1 && nc>=1 && nc<=self->nt
      && (size_t)bsp.len == (size_t)nc*2u*bands[0]*sizeof(float);
  }
  if(!valid){
    PyBuffer_Release(&bsp); PyBuffer_Release(&boff); PyBuffer_Release(&bmem);
    PyErr_SetString(PyExc_ValueError,"set_tier0_clusters: invalid specs, offsets or members buffer shape");
    return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_hmf_set_tier0_clusters(self->p,nc,(const float*)bsp.buf,
                              (const int*)boff.buf,(const int*)bmem.buf,lag_pad);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&bsp); PyBuffer_Release(&boff); PyBuffer_Release(&bmem);
  return PyBool_FromLong(r==0);
}
static PyObject *HMF_clear_tier0_clusters(HMFObject *self,PyObject *unused){
  (void)unused;
  ap_hmf_clear_tier0_clusters(self->p);
  Py_RETURN_NONE;
}
static PyObject *HMF_tier0_cluster_count(HMFObject *self,PyObject *unused){
  (void)unused;
  return PyLong_FromLong(ap_hmf_tier0_cluster_count(self->p));
}
static PyObject *HMF_set_tier1_clusters(HMFObject *self,PyObject *args){
  Py_buffer bsp,boff,bmem;
  int lag_pad=0;
  if(!PyArg_ParseTuple(args,"y*y*y*|i",&bsp,&boff,&bmem,&lag_pad)) return NULL;
  size_t bands[AP_HMF_MAX_TIERS];
  int nti=ap_hmf_chain(self->p,bands);
  int valid = boff.len%(Py_ssize_t)sizeof(int)==0
    && boff.len>=2*(Py_ssize_t)sizeof(int)
    && bmem.len==(Py_ssize_t)self->nt*(Py_ssize_t)sizeof(int);
  int nc = valid ? (int)(boff.len/(Py_ssize_t)sizeof(int))-1 : 0;
  if(valid){
    valid = nti>=2 && nc>=1 && nc<=self->nt
      && (size_t)bsp.len == (size_t)nc*2u*bands[1]*sizeof(float);
  }
  if(!valid){
    PyBuffer_Release(&bsp); PyBuffer_Release(&boff); PyBuffer_Release(&bmem);
    PyErr_SetString(PyExc_ValueError,"set_tier1_clusters: invalid specs, offsets or members buffer shape");
    return NULL;
  }
  int r;
  Py_BEGIN_ALLOW_THREADS
  r=ap_hmf_set_tier1_clusters(self->p,nc,(const float*)bsp.buf,
                              (const int*)boff.buf,(const int*)bmem.buf,lag_pad);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&bsp); PyBuffer_Release(&boff); PyBuffer_Release(&bmem);
  return PyBool_FromLong(r==0);
}
static PyObject *HMF_clear_tier1_clusters(HMFObject *self,PyObject *unused){
  (void)unused;
  ap_hmf_clear_tier1_clusters(self->p);
  Py_RETURN_NONE;
}
static PyObject *HMF_tier1_cluster_count(HMFObject *self,PyObject *unused){
  (void)unused;
  return PyLong_FromLong(ap_hmf_tier1_cluster_count(self->p));
}

static PyObject *HMF_set_hermitian(HMFObject *self,PyObject *args){
  int h;
  if(!PyArg_ParseTuple(args,"p",&h)) return NULL;
  if(ap_hmf_set_hermitian(self->p,h)<0){
    PyErr_SetString(PyExc_RuntimeError,"failed to set hermitian mode");
    return NULL;
  }
  Py_RETURN_NONE;
}

GUARDED(HMFObject,HMF_series_group)
GUARDED(HMFObject,HMF_set_taps)
GUARDED(HMFObject,HMF_set_real_series)
GUARDED(HMFObject,HMF_set_direct)
GUARDED(HMFObject,HMF_direct_stats)
GUARDED(HMFObject,HMF_price_direct_pair)
GUARDED(HMFObject,HMF_set_direct_prices)
GUARDED(HMFObject,HMF_set_q15)
GUARDED(HMFObject,HMF_q15_stats)
GUARDED(HMFObject,HMF_set_tier0_clusters)
GUARDED(HMFObject,HMF_clear_tier0_clusters)
GUARDED(HMFObject,HMF_tier0_cluster_count)
GUARDED(HMFObject,HMF_set_tier1_clusters)
GUARDED(HMFObject,HMF_clear_tier1_clusters)
GUARDED(HMFObject,HMF_tier1_cluster_count)
GUARDED(HMFObject,HMF_set_data)
GUARDED(HMFObject,HMF_set_template)
GUARDED(HMFObject,HMF_set_data_batch)
GUARDED(HMFObject,HMF_set_template_batch)
GUARDED(HMFObject,HMF_set_reference)
GUARDED(HMFObject,HMF_set_thresholds)
GUARDED(HMFObject,HMF_set_hermitian)
GUARDED(HMFObject,HMF_run)
GUARDED(HMFObject,HMF_nbins)
GUARDED(HMFObject,HMF_run_series)
GUARDED(HMFObject,HMF_run_series_sparse)
GUARDED(HMFObject,HMF_stats)
GUARDED(HMFObject,HMF_chain)
GUARDED(HMFObject,HMF_band_offsets)
GUARDED(HMFObject,HMF_set_band_offsets)
GUARDED(HMFObject,HMF_thresholds)
GUARDED(HMFObject,HMF_series_ticks)
GUARDED(HMFObject,HMF_tier_stats)
GUARDED(HMFObject,HMF_tier_inputs)
static PyMethodDef HMF_methods[]={
  {"series_group",(PyCFunction)HMF_series_group_g,METH_NOARGS,"actual series block group"},
  {"set_taps",(PyCFunction)HMF_set_taps_g,METH_VARARGS,"set_taps(taps float32 (nt, stride), stride, counts int64 (nt,)): each template's real FIR taps"},
  {"set_real_series",(PyCFunction)HMF_set_real_series_g,METH_VARARGS,"set_real_series(on, stride=1) -> True if run_series now reads real float32 series (half-size block transforms); stride 2 reads one lane of a complex series"},
  {"set_direct",(PyCFunction)HMF_set_direct_g,METH_VARARGS,"set_direct(on, halfwidth=1) -> True if survivors are now refined by direct correlation where cheaper"},
  {"direct_stats",(PyCFunction)HMF_direct_stats_g,METH_NOARGS,"direct refine counters and prices"},
  {"price_direct_pair",(PyCFunction)HMF_price_direct_pair_g,METH_NOARGS,"price_direct_pair() -> (ticks per lag x tap, ticks per transform pair) timed on this plan's kernels, or None"},
  {"set_direct_prices",(PyCFunction)HMF_set_direct_prices_g,METH_VARARGS,"set_direct_prices(lagtap, fftpair) -> True: the prices the direct-or-transform choice compares"},
  {"set_q15",(PyCFunction)HMF_set_q15_g,METH_VARARGS,"set_q15(on) -> True if the first tier now runs behind the Q15 screen"},
  {"q15_stats",(PyCFunction)HMF_q15_stats_g,METH_NOARGS,"q15_stats() -> (on, pairs passed to the float tier, screen ticks)"},
  {"set_tier0_clusters",(PyCFunction)HMF_set_tier0_clusters_g,METH_VARARGS,"set_tier0_clusters(specs, offsets, members, lag_pad=0) -> True if Tier-0 screener gating is active"},
  {"clear_tier0_clusters",(PyCFunction)HMF_clear_tier0_clusters_g,METH_NOARGS,"clear_tier0_clusters() -> disable Tier-0 screener gating"},
  {"tier0_cluster_count",(PyCFunction)HMF_tier0_cluster_count_g,METH_NOARGS,"tier0_cluster_count() -> active Tier-0 screener count, or 0 if unclustered"},
  {"set_tier1_clusters",(PyCFunction)HMF_set_tier1_clusters_g,METH_VARARGS,"set_tier1_clusters(specs, offsets, members, lag_pad=0) -> True if Tier-1 sub-screener gating is active (requires Tier-0 clusters; each Tier-1 cluster must lie inside one Tier-0 cluster)"},
  {"clear_tier1_clusters",(PyCFunction)HMF_clear_tier1_clusters_g,METH_NOARGS,"clear_tier1_clusters() -> disable Tier-1 screener gating"},
  {"tier1_cluster_count",(PyCFunction)HMF_tier1_cluster_count_g,METH_NOARGS,"tier1_cluster_count() -> active Tier-1 screener count, or 0 if unclustered"},
  {"set_data",(PyCFunction)HMF_set_data_g,METH_VARARGS,"set_data(i, buffer)"},
  {"set_template",(PyCFunction)HMF_set_template_g,METH_VARARGS,"set_template(i, buffer)"},
  {"set_data_batch",(PyCFunction)HMF_set_data_batch_g,METH_VARARGS,"set_data_batch(i0, buffer)"},
  {"set_template_batch",(PyCFunction)HMF_set_template_batch_g,METH_VARARGS,"set_template_batch(i0, buffer)"},
  {"set_reference",(PyCFunction)HMF_set_reference_g,METH_VARARGS,"set_reference(buffer|None)"},
  {"set_thresholds",(PyCFunction)HMF_set_thresholds_g,METH_VARARGS,"set_thresholds([t per tier]); negative = unconfigured"},
  {"set_hermitian",(PyCFunction)HMF_set_hermitian_g,METH_VARARGS,"set_hermitian(bool)"},
  {"run",(PyCFunction)HMF_run_g,METH_VARARGS,"run(...) -> total crossings"},
  {"nbins",(PyCFunction)HMF_nbins_g,METH_VARARGS,"nbins(binsize, start, end)"},
  {"run_series",(PyCFunction)HMF_run_series_g,METH_VARARGS,"run_series(...)"},
  {"run_series_sparse",(PyCFunction)HMF_run_series_sparse_g,METH_VARARGS,
   "run_series_sparse(series,starts,wstart,wend,t0,nt,binsize,thr,cnt|None) -> (flat,index,value bytes,total)"},
  {"run_series_batch_sparse",(PyCFunction)HMF_run_series_batch_sparse,METH_O|METH_STATIC,
   "run_series_batch_sparse(jobs) -> [(flat,index,value bytes,total), ...]"},
  {"stats",(PyCFunction)HMF_stats_g,METH_NOARGS,"stats() -> (pairs, refined)"},
  {"chain",(PyCFunction)HMF_chain_g,METH_NOARGS,"chain() -> bands"},
  {"band_offsets",(PyCFunction)HMF_band_offsets_g,METH_NOARGS,"band_offsets() -> per-tier starting fine bins"},
  {"set_band_offsets",(PyCFunction)HMF_set_band_offsets_g,METH_VARARGS,"set_band_offsets([k0 per tier])"},
  {"thresholds",(PyCFunction)HMF_thresholds_g,METH_NOARGS,"thresholds() -> per-tier thresholds in force"},
  {"series_ticks",(PyCFunction)HMF_series_ticks_g,METH_NOARGS,"series_ticks() -> ticks spent in run_series calls"},
  {"tier_stats",(PyCFunction)HMF_tier_stats_g,METH_NOARGS,"[(band, passed, ticks) per tier] + [(n, refined, ticks)]"},
  {"tier_inputs",(PyCFunction)HMF_tier_inputs_g,METH_NOARGS,"Actual input counts per logical gate"},
  {NULL}
};
static PyObject *HMF_get_n(HMFObject *self, void *closure){
  (void)closure;
  return PyLong_FromSsize_t(self->n);
}
static PyObject *HMF_get_k(HMFObject *self, void *closure){
  (void)closure;
  return PyLong_FromSsize_t(self->k);
}
BUSY_GETTER(HMFObject)
static PyGetSetDef HMF_getset[] = {
  {"_busy", (getter)HMFObject_get_busy, NULL, "a method is running on this object", NULL},
  {"n", (getter)HMF_get_n, NULL, "full FFT size", NULL},
  {"k", (getter)HMF_get_k, NULL, "template bins", NULL},
  {NULL}
};
static PyTypeObject HMFType={
  PyVarObject_HEAD_INIT(NULL,0)
  .tp_name="matchedfilter._core.HMF", .tp_basicsize=sizeof(HMFObject),
  .tp_flags=Py_TPFLAGS_DEFAULT, .tp_new=PyType_GenericNew,
  .tp_init=(initproc)HMF_init, .tp_dealloc=(destructor)HMF_dealloc,
  .tp_methods=HMF_methods, .tp_getset=HMF_getset, .tp_doc="matchedfilter hierarchical matched filter (opaque)",
};


/* ---------------- the step table: gated leaf steps and single-template steps ---------------- */
/* HMFTable holds a call shape's leaf work, compiled once. A gated step is one
   ap_hmf_sparse_job (a template group's blocks of one bin count, on one plan) with its block
   layout, plus what it needs to be set up and assembled. A single-template step is one
   template group as a follow-up filters it, one template at a time (src/followup.c): its
   block geometry, its templates' taps (or spectra) and bank indices, and the group's store of
   template spectra, which every table compiled from the group shares. run() binds the gated
   steps' series, sets each plan to the step's series mode and direct prices, clusters the
   steps of each phase by the bytes their series spans share (as the batch's caller once did
   in Python), runs every phase with ap_hmf_run_series_batch_sparse; then runs the calls bound
   to the single-template steps (a template, a series, windows, a bin size and a threshold per
   call) together, with the follow-up kernel; and assembles the peaks of each job (bank call)
   into one arena: template index, sample, complex SNR, block start and block length, in the
   order FilterResults had them, window bins merged. A flat step is a template group's blocks
   of one bin count on an ungated plan (MF: a flat bank's, or a hierarchical bank's call below
   its threshold): run() runs it with ap_mf_run_series after the gated phases, widening a real
   series to complex over the span its blocks read, and assembles its peaks as a gated step's.
   A table may hold a schedule (hmf_run_schedule): an order of its correlation steps and of
   block ranges of its leaf steps (phase -1) with zeroing, scaling, copies and carried collars
   between them, the tiled middle-to-leaf cascade; run() then runs the schedule in place of
   "every correlation step first", and the other leaf steps after it. */
static inline int64_t wbk_bin_f(double a, double b);
typedef struct {
  HMFObject *hmf;
  int slot, real, stride, phase, job, has_prices;
  double lagtap, fftpair;
  size_t *starts, *low, *high;   /* the job's block layout, owned */
  unsigned *bin_phase;           /* owned, or NULL */
  int nblocks, nt;
  size_t nbins, binsize, block_len;
  float threshold;
  int64_t *tmap;                 /* [nt] bank template index of each plan template */
  int64_t *order;                /* [nblocks] output row of each computed row, or NULL */
  int64_t *ostarts;              /* [nblocks] block starts in output order */
  int64_t s_min, s_max;          /* least and greatest block start */
  Py_buffer stats;               /* the plan's pending batch times (MatchedFilter._step_stats) */
  int has_stats;
} hmf_step;
/* A flat step: one ap_mf_run_series call of an ungated plan over a template group's blocks of
   one bin count, in the caller's block order (an ungated plan of one data row does not group
   its blocks). real and stride are the slot's series kind the step was compiled for. */
typedef struct {
  MFObject *mf;
  int slot, real, stride, job;
  size_t *starts, *low, *high;   /* the block layout, owned */
  unsigned *bin_phase;           /* owned, or NULL */
  int nblocks, nt;
  size_t nbins, binsize, block_len;
  float threshold;
  int64_t *tmap;                 /* [nt] bank template index of each plan template */
  int64_t *ostarts;              /* [nblocks] block starts */
  size_t s_min, s_max;           /* least and greatest block start */
  Py_buffer stats;               /* the plan's pending batch times (MatchedFilter._step_stats) */
  int has_stats;
} hmf_flat_step;
/* A flat step's peaks as a run kept them: per peak its flat (block, template, bin) index, its
   lag in the block and its value (re, im); malloc'd. */
typedef struct { int64_t *flat, *idx; float *val; size_t count; int total; } hmf_flat_out;
/* A correlation step: one ap_mf_correlate_series_continuous call (its real-series form for a
   float32 series) of a correlation plan's templates [t0, t0 + nt) over some of its blocks of
   one input slot's series, into nt rows of an output slot; then the sample runs it clears are
   zeroed on those rows, and when the step reads a scale vector of the run, each row is scaled
   over its scale runs. Rows given (rows) are written through a scratch of nt rows and copied
   to those rows whole, after the clearing and scaling. */
typedef struct {
  MFObject *mf;
  int slot, real;                /* input slot; real: a float32 series, half-size transforms */
  int out, row0;                 /* output slot, and its first row when rows is NULL */
  int64_t *rows;                 /* [nt] output row of each template, or NULL */
  int t0, nt, nblocks;
  size_t *starts, *bounds;       /* [nblocks], [2 * nblocks] or NULL: block layout, owned */
  size_t lo, hi;                 /* the plan's valid span of a block */
  int64_t *clear; Py_ssize_t nclear;        /* [2 * nclear] sample runs zeroed */
  int scale;                     /* index of the run's scale vector, or -1 */
  int64_t *scale_index;          /* [nt] each row's entry of that vector */
  int64_t *scale_runs; Py_ssize_t nscale_runs;  /* [2 * nscale_runs] sample runs scaled */
} hmf_corr_step;
typedef struct {
  int64_t *win_starts; Py_ssize_t nwin;   /* the call's window starts, for merging bins */
  Py_ssize_t *merge_bs; int nmerge;       /* bin sizes whose partial bins merge, in order */
} hmf_table_job;
/* A template group's store of template spectra (SpectrumStore(slots, n)), shared by every
   table compiled from the group: up to `slots` spectra of n bins, each slot allocated when a
   template first takes it, the least recently used given up first. It holds nothing for a
   template never asked for. */
typedef struct {
  PyObject_HEAD
  int cap, nalloc;               /* slots allowed; slots allocated (0..nalloc-1) */
  size_t n;
  int *row_of;                   /* [cap] the row a slot holds */
  int64_t *used;                 /* [cap] the slot's last use on clock */
  char *ready;                   /* [cap] whether it holds that row's spectrum */
  float **spec;                  /* [cap] its spectrum (2n floats, 64-byte aligned) */
  int64_t clock;
  int busy;                      /* a run holds the store (set and cleared with the GIL held) */
} SpectrumStoreObject;
static void SpectrumStore_dealloc(SpectrumStoreObject *self){
  if(self->spec) for(int k=0;k<self->nalloc;k++) free(self->spec[k]);
  PyMem_Free(self->spec); PyMem_Free(self->row_of); PyMem_Free(self->used); PyMem_Free(self->ready);
  Py_TYPE(self)->tp_free((PyObject*)self);
}
static int SpectrumStore_init(SpectrumStoreObject *self,PyObject *args,PyObject *kw){
  (void)kw; int cap; Py_ssize_t n;
  if(!PyArg_ParseTuple(args,"in",&cap,&n)) return -1;
  if(self->spec){ PyErr_SetString(PyExc_RuntimeError,"SpectrumStore: already initialised"); return -1; }
  if(cap<1 || n<1){ PyErr_SetString(PyExc_ValueError,"SpectrumStore: slots and bins must be positive"); return -1; }
  self->cap=cap; self->n=(size_t)n;
  self->row_of=PyMem_Calloc((size_t)cap,sizeof(int)); self->used=PyMem_Calloc((size_t)cap,sizeof(int64_t));
  self->ready=PyMem_Calloc((size_t)cap,1); self->spec=PyMem_Calloc((size_t)cap,sizeof(float*));
  if(!self->row_of||!self->used||!self->ready||!self->spec){ PyErr_NoMemory(); return -1; }
  return 0;
}
static PyObject *SpectrumStore_get_held(SpectrumStoreObject *self,void *closure){
  (void)closure; return PyLong_FromLong(self->nalloc);
}
static PyGetSetDef SpectrumStore_getset[]={
  {"held",(getter)SpectrumStore_get_held,NULL,"the slots allocated (spectra held or being made)",NULL},
  {NULL,NULL,NULL,NULL,NULL}
};
static PyTypeObject SpectrumStoreType={
  PyVarObject_HEAD_INIT(NULL,0)
  .tp_name="matchedfilter._core.SpectrumStore", .tp_basicsize=sizeof(SpectrumStoreObject),
  .tp_flags=Py_TPFLAGS_DEFAULT, .tp_new=PyType_GenericNew,
  .tp_init=(initproc)SpectrumStore_init, .tp_dealloc=(destructor)SpectrumStore_dealloc,
  .tp_getset=SpectrumStore_getset,
  .tp_doc="a template group's store of template spectra: SpectrumStore(slots, n)",
};

/* A single-template step: a template group's templates as the follow-up kernel filters them.
   A template whose row of spectrum_rows is not negative has its spectrum given (spectra);
   the others are made from their taps when a run needs them, into a slot of the group's
   store (SpectrumStore). The arrays are the group's, held as views, not copied. */
typedef struct {
  Py_buffer taps, counts, spectra, spectrum_rows, tmap_view;
  int held;                      /* the views held: 1 taps, 2 counts, 4 spectra, 8 rows, 16 tmap */
  SpectrumStoreObject *store;    /* a reference, or NULL */
  int nt, tr_cplx;
  size_t n; int64_t step, c_bad;
  Py_ssize_t row_floats;         /* floats per row of taps */
  const int64_t *tmap;           /* [nt] bank template index of each row (tmap_view) */
} hmf_single;
typedef struct {
  PyObject_HEAD
  hmf_step *steps; int nsteps;
  hmf_table_job *jobs; int njobs;
  int nslots;
  hmf_single *singles; int nsingles;
  hmf_flat_step *flats; int nflats;
  hmf_corr_step *corrs; int ncorrs;
  int nouts;                     /* the correlation steps' output slots */
  int64_t *ops; int nops;        /* the schedule: HMF_OP_FIELDS int64 per op, or NULL */
  int64_t *sargs; Py_ssize_t nsargs;  /* the ops' runs, rows and slices */
} HMFTableObject;
/* A schedule op is HMF_OP_FIELDS int64: its kind, then its fields (hmf_run_schedule). */
#define HMF_OP_FIELDS 12

static void hmf_table_free_contents(HMFTableObject *self){
  if(self->singles){
    for(int i=0;i<self->nsingles;i++){
      hmf_single *g=&self->singles[i];
      if(g->held&1) PyBuffer_Release(&g->taps);
      if(g->held&2) PyBuffer_Release(&g->counts);
      if(g->held&4) PyBuffer_Release(&g->spectra);
      if(g->held&8) PyBuffer_Release(&g->spectrum_rows);
      if(g->held&16) PyBuffer_Release(&g->tmap_view);
      Py_XDECREF(g->store);
    }
    PyMem_Free(self->singles);
  }
  self->singles=NULL; self->nsingles=0;
  if(self->flats){
    for(int i=0;i<self->nflats;i++){
      hmf_flat_step *f=&self->flats[i];
      Py_XDECREF(f->mf);
      PyMem_Free(f->starts); PyMem_Free(f->low); PyMem_Free(f->high); PyMem_Free(f->bin_phase);
      PyMem_Free(f->tmap); PyMem_Free(f->ostarts);
      if(f->has_stats) PyBuffer_Release(&f->stats);
    }
    PyMem_Free(self->flats);
  }
  self->flats=NULL; self->nflats=0;
  if(self->corrs){
    for(int i=0;i<self->ncorrs;i++){
      hmf_corr_step *c=&self->corrs[i];
      Py_XDECREF(c->mf);
      PyMem_Free(c->rows); PyMem_Free(c->starts); PyMem_Free(c->bounds); PyMem_Free(c->clear);
      PyMem_Free(c->scale_index); PyMem_Free(c->scale_runs);
    }
    PyMem_Free(self->corrs);
  }
  self->corrs=NULL; self->ncorrs=0;
  if(self->steps){
    for(int i=0;i<self->nsteps;i++){
      hmf_step *s=&self->steps[i];
      Py_XDECREF(s->hmf);
      PyMem_Free(s->starts); PyMem_Free(s->low); PyMem_Free(s->high); PyMem_Free(s->bin_phase);
      PyMem_Free(s->tmap); PyMem_Free(s->order); PyMem_Free(s->ostarts);
      if(s->has_stats) PyBuffer_Release(&s->stats);
    }
    PyMem_Free(self->steps);
  }
  if(self->jobs){
    for(int j=0;j<self->njobs;j++){ PyMem_Free(self->jobs[j].win_starts); PyMem_Free(self->jobs[j].merge_bs); }
    PyMem_Free(self->jobs);
  }
  self->steps=NULL; self->jobs=NULL; self->nsteps=self->njobs=0;
  PyMem_Free(self->ops); PyMem_Free(self->sargs);
  self->ops=NULL; self->sargs=NULL; self->nops=0; self->nsargs=0;
}
static void HMFTable_dealloc(HMFTableObject *self){
  hmf_table_free_contents(self);
  Py_TYPE(self)->tp_free((PyObject*)self);
}
/* A copy of a C-contiguous buffer of count elements of size item, or NULL with the exception
   set. None gives NULL with no exception when allow_none. */
static void *hmf_table_copy(PyObject *o,Py_ssize_t count,Py_ssize_t item,int allow_none,int *failed){
  *failed=0;
  if(o==Py_None){
    if(allow_none) return NULL;
    PyErr_SetString(PyExc_ValueError,"HMFTable: an array is required"); *failed=1; return NULL;
  }
  Py_buffer b;
  if(PyObject_GetBuffer(o,&b,PyBUF_C_CONTIGUOUS)<0){ *failed=1; return NULL; }
  if(b.len!=count*item){
    PyBuffer_Release(&b);
    PyErr_SetString(PyExc_ValueError,"HMFTable: an array has the wrong length"); *failed=1;
    return NULL;
  }
  void *out=PyMem_Malloc(count*item>0?(size_t)(count*item):1);
  if(!out){ PyBuffer_Release(&b); PyErr_NoMemory(); *failed=1; return NULL; }
  if(count) memcpy(out,b.buf,(size_t)(count*item));
  PyBuffer_Release(&b);
  return out;
}
/* A single-template step from its tuple (n, step, c_bad, tmap, taps|None, counts|None,
   spectra|None, spectrum_rows|None, store|None); see hmf_single. 0, or -1 with the
   exception set. */
static int hmf_single_init(hmf_single *g,PyObject *item){
  Py_ssize_t n,step,c_bad; PyObject *tmap,*taps,*counts,*spectra,*rows,*store;
  memset(g,0,sizeof(*g));
  if(!PyArg_ParseTuple(item,"nnnOOOOOO",&n,&step,&c_bad,&tmap,&taps,&counts,&spectra,&rows,
                       &store)) return -1;
  if(n<16 || (n&(n-1)) || !ap_supported((size_t)n) || step<1 || c_bad<0){
    PyErr_SetString(PyExc_ValueError,"HMFTable: a single-template step's block geometry is invalid");
    return -1;
  }
  g->n=(size_t)n; g->step=(int64_t)step; g->c_bad=(int64_t)c_bad;
  if(PyObject_GetBuffer(tmap,&g->tmap_view,PyBUF_C_CONTIGUOUS)<0) return -1;
  g->held|=16;
  const Py_ssize_t nt=g->tmap_view.len/8;
  if(nt<1 || nt>INT_MAX || g->tmap_view.len%8){ PyErr_SetString(PyExc_ValueError,"HMFTable: a single-template step needs templates"); return -1; }
  g->nt=(int)nt; g->tmap=g->tmap_view.buf;
  const char *bad="HMFTable: a single-template step's templates are invalid";
  if(spectra!=Py_None){
    if(PyObject_GetBuffer(spectra,&g->spectra,PyBUF_C_CONTIGUOUS)<0) return -1;
    g->held|=4;
    if(PyObject_GetBuffer(rows,&g->spectrum_rows,PyBUF_C_CONTIGUOUS)<0) return -1;
    g->held|=8;
    if(g->spectrum_rows.len!=nt*8 || g->spectra.len%(n*8)){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
    const int64_t *r=g->spectrum_rows.buf; const Py_ssize_t ns=g->spectra.len/(n*8);
    for(Py_ssize_t i=0;i<nt;i++)
      if(r[i]>=ns || (r[i]<0 && taps==Py_None)){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
  }
  if(taps!=Py_None){
    if(PyObject_GetBuffer(taps,&g->taps,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return -1;
    g->held|=1;
    const char *f=g->taps.format?g->taps.format:"B";
    if(*f=='<' || *f=='=' || *f=='@') f++;
    if(g->taps.ndim!=2 || g->taps.shape[0]!=nt || !(( !strcmp(f,"f") && g->taps.itemsize==4)
                                                      || (!strcmp(f,"Zf") && g->taps.itemsize==8))){
      PyErr_SetString(PyExc_ValueError,"HMFTable: taps must be (templates, taps) float32 or complex64");
      return -1;
    }
    g->tr_cplx=g->taps.itemsize==8;
    g->row_floats=g->taps.shape[1]*(g->taps.itemsize/4);
    if(PyObject_GetBuffer(counts,&g->counts,PyBUF_C_CONTIGUOUS)<0) return -1;
    g->held|=2;
    if(!PyObject_TypeCheck(store,&SpectrumStoreType) || !((SpectrumStoreObject*)store)->spec
       || ((SpectrumStoreObject*)store)->n!=(size_t)n){
      PyErr_SetString(PyExc_ValueError,"HMFTable: a step with taps needs its group's SpectrumStore of n bins");
      return -1;
    }
    Py_INCREF(store); g->store=(SpectrumStoreObject*)store;
    if(g->counts.len!=nt*8){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
    const int64_t *c=g->counts.buf, *r=(g->held&8)?g->spectrum_rows.buf:NULL;
    for(Py_ssize_t i=0;i<nt;i++)
      if((!r || r[i]<0) && (c[i]<1 || c[i]>n || c[i]>g->taps.shape[1])){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
  } else if(spectra==Py_None){
    PyErr_SetString(PyExc_ValueError,bad); return -1;
  }
  for(Py_ssize_t i=0;i<nt;i++) if(g->tmap[i]<0){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
  return 0;
}
/* A table copy of an int64 (k, 2) array of sample runs (None: no runs), each [a, b) with
   0 <= a <= b. 0, or -1 with the exception set. */
static int hmf_runs_copy(PyObject *o,int64_t **runs,Py_ssize_t *count){
  *runs=NULL; *count=0;
  if(o==Py_None) return 0;
  Py_buffer b;
  if(PyObject_GetBuffer(o,&b,PyBUF_C_CONTIGUOUS)<0) return -1;
  const Py_ssize_t len=b.len;
  PyBuffer_Release(&b);
  if(len%16){ PyErr_SetString(PyExc_ValueError,"HMFTable: sample runs must be (k, 2) int64"); return -1; }
  int failed;
  *runs=hmf_table_copy(o,len/8,8,0,&failed);
  if(failed) return -1;
  *count=len/16;
  for(Py_ssize_t k=0;k<*count;k++)
    if((*runs)[2*k]<0 || (*runs)[2*k+1]<(*runs)[2*k]){
      PyErr_SetString(PyExc_ValueError,"HMFTable: a sample run is invalid"); return -1;
    }
  return 0;
}
/* A correlation step from its tuple (mf, slot, real, out, row0, rows|None, t0, nt,
   starts|None, bounds|None, lo, hi, clear|None, scale, scale_index|None, scale_runs|None);
   see hmf_corr_step. uintp starts and bounds, int64 rows, runs and
   scale indices. 0, or -1 with the exception set. */
static int hmf_corr_init(hmf_corr_step *c,PyObject *item,int nslots,int nouts){
  PyObject *rows,*st,*bnd,*clear,*sidx,*sruns; MFObject *mf; Py_ssize_t lo,hi;
  memset(c,0,sizeof(*c));
  if(!PyArg_ParseTuple(item,"O!iiiiOiiOOnnOiOO",&MFType,&mf,&c->slot,&c->real,&c->out,&c->row0,
                       &rows,&c->t0,&c->nt,&st,&bnd,&lo,&hi,&clear,&c->scale,&sidx,&sruns))
    return -1;
  Py_INCREF(mf); c->mf=mf;
  const char *bad="HMFTable: a correlation step's slots, templates or block layout are invalid";
  if(c->slot<0 || c->slot>=nslots || c->out<0 || c->out>=nouts || c->row0<0 || c->nt<1
     || !ap_range_ok(c->t0,c->nt,mf->nt) || lo<0 || lo>=hi || hi>mf->n || c->scale<-1){
    PyErr_SetString(PyExc_ValueError,bad); return -1;
  }
  c->lo=(size_t)lo; c->hi=(size_t)hi;
  int failed;
  if(rows!=Py_None){
    c->rows=hmf_table_copy(rows,c->nt,8,0,&failed); if(failed) return -1;
    for(int t=0;t<c->nt;t++) if(c->rows[t]<0){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
  }
  if(st!=Py_None){
    Py_buffer b;
    if(PyObject_GetBuffer(st,&b,PyBUF_C_CONTIGUOUS)<0) return -1;
    const Py_ssize_t nb=b.len/(Py_ssize_t)sizeof(size_t);
    PyBuffer_Release(&b);
    if(nb>INT_MAX){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
    c->nblocks=(int)nb;
    c->starts=hmf_table_copy(st,nb,sizeof(size_t),0,&failed); if(failed) return -1;
    c->bounds=hmf_table_copy(bnd,2*nb,sizeof(size_t),1,&failed); if(failed) return -1;
    for(int k=0;k<c->nblocks;k++){
      if(c->starts[k]>SIZE_MAX-(size_t)mf->n
         || (c->bounds && (c->bounds[2*k]<c->lo || c->bounds[2*k]>=c->bounds[2*k+1]
                           || c->bounds[2*k+1]>c->hi))){
        PyErr_SetString(PyExc_ValueError,bad); return -1;
      }
    }
  }
  if(hmf_runs_copy(clear,&c->clear,&c->nclear)) return -1;
  if(c->scale>=0){
    c->scale_index=hmf_table_copy(sidx,c->nt,8,0,&failed); if(failed) return -1;
    for(int t=0;t<c->nt;t++) if(c->scale_index[t]<0){ PyErr_SetString(PyExc_ValueError,bad); return -1; }
    if(hmf_runs_copy(sruns,&c->scale_runs,&c->nscale_runs)) return -1;
  }
  return 0;
}
/* HMFTable(steps, jobs, nslots, singles=(), flats=(), corrs=(), nouts=0). Each step is (hmf, slot, real, stride,
   starts, low, high, bin_phase|None, nt, binsize, threshold, prices|None, phase, job, tmap,
   order|None, ostarts[, stats]): uintp starts and windows, uint32 phases, int64 tmap, order and
   ostarts; prices are the (lagtap, fftpair) the plan runs this series mode with, or None to
   leave them. Each job is (window starts int64, merge bin sizes). Each single is a
   single-template step's tuple (hmf_single_init). Each flat step is (mf, slot, real, stride,
   starts, low, high, bin_phase|None, nt, binsize, threshold, job, tmap, ostarts, stats|None),
   in job order. Each correlation step is a tuple of hmf_corr_init's, writing into one of
   nouts output slots. */
static int HMFTable_init(HMFTableObject *self,PyObject *args,PyObject *kw){
  (void)kw;
  PyObject *steps_arg,*jobs_arg,*singles_arg=NULL,*flats_arg=NULL,*corrs_arg=NULL,*sched_arg=NULL;
  int nslots,nouts=0;
  if(!PyArg_ParseTuple(args,"OOi|OOOiO",&steps_arg,&jobs_arg,&nslots,&singles_arg,&flats_arg,
                       &corrs_arg,&nouts,&sched_arg))
    return -1;
  hmf_table_free_contents(self);
  self->nouts=nouts;
  if(sched_arg && sched_arg!=Py_None){
    PyObject *o,*a; int failed;
    if(!PyArg_ParseTuple(sched_arg,"OO",&o,&a)) return -1;
    Py_buffer bo,ba;
    if(PyObject_GetBuffer(o,&bo,PyBUF_C_CONTIGUOUS)<0) return -1;
    const Py_ssize_t no=bo.len/8; PyBuffer_Release(&bo);
    if(PyObject_GetBuffer(a,&ba,PyBUF_C_CONTIGUOUS)<0) return -1;
    const Py_ssize_t na=ba.len/8; PyBuffer_Release(&ba);
    if(no%HMF_OP_FIELDS || no/HMF_OP_FIELDS>INT_MAX){
      PyErr_SetString(PyExc_ValueError,"HMFTable: a schedule is (ops int64 of 12 fields each, args int64)");
      return -1;
    }
    self->ops=hmf_table_copy(o,no,8,0,&failed);
    if(failed) return -1;
    self->sargs=hmf_table_copy(a,na,8,0,&failed);
    if(failed) return -1;
    self->nops=(int)(no/HMF_OP_FIELDS); self->nsargs=na;
  }
  if(corrs_arg){
    PyObject *corrs=PySequence_Fast(corrs_arg,"corrs must be a sequence");
    if(!corrs) return -1;
    const Py_ssize_t nc=PySequence_Fast_GET_SIZE(corrs);
    if(nc>INT_MAX || nouts<0 || nslots<0){
      Py_DECREF(corrs); PyErr_SetString(PyExc_ValueError,"HMFTable: too many correlation steps");
      return -1;
    }
    self->corrs=PyMem_Calloc(nc?(size_t)nc:1,sizeof(hmf_corr_step));
    if(!self->corrs){ Py_DECREF(corrs); PyErr_NoMemory(); return -1; }
    for(Py_ssize_t i=0;i<nc;i++){
      self->ncorrs=(int)i+1;
      if(hmf_corr_init(&self->corrs[i],PySequence_Fast_GET_ITEM(corrs,i),nslots,nouts)){
        Py_DECREF(corrs); hmf_table_free_contents(self); return -1;
      }
    }
    Py_DECREF(corrs);
  }
  if(singles_arg){
    PyObject *singles=PySequence_Fast(singles_arg,"singles must be a sequence");
    if(!singles) return -1;
    const Py_ssize_t ng=PySequence_Fast_GET_SIZE(singles);
    self->singles=PyMem_Calloc(ng?(size_t)ng:1,sizeof(hmf_single));
    if(!self->singles){ Py_DECREF(singles); PyErr_NoMemory(); return -1; }
    for(Py_ssize_t i=0;i<ng && i<INT_MAX;i++){
      self->nsingles=(int)i+1;
      if(hmf_single_init(&self->singles[i],PySequence_Fast_GET_ITEM(singles,i))){
        Py_DECREF(singles); hmf_table_free_contents(self); return -1;
      }
    }
    Py_DECREF(singles);
  }
  PyObject *flats=NULL;
  PyObject *steps=PySequence_Fast(steps_arg,"steps must be a sequence");
  if(!steps) return -1;
  PyObject *jobs=PySequence_Fast(jobs_arg,"jobs must be a sequence");
  if(!jobs){ Py_DECREF(steps); return -1; }
  const Py_ssize_t ns=PySequence_Fast_GET_SIZE(steps), nj=PySequence_Fast_GET_SIZE(jobs);
  int rc=-1;
  if(ns>INT_MAX || nj>INT_MAX || nslots<0){ PyErr_SetString(PyExc_ValueError,"HMFTable: too many steps"); goto done; }
  self->steps=PyMem_Calloc(ns?(size_t)ns:1,sizeof(hmf_step));
  self->jobs=PyMem_Calloc(nj?(size_t)nj:1,sizeof(hmf_table_job));
  if(!self->steps||!self->jobs){ PyErr_NoMemory(); goto done; }
  self->nslots=nslots;
  for(Py_ssize_t j=0;j<nj;j++){
    PyObject *w,*mb; int failed;
    if(!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(jobs,j),"OO",&w,&mb)) goto done;
    hmf_table_job *J=&self->jobs[j];
    self->njobs=(int)j+1;
    Py_buffer bw;
    if(PyObject_GetBuffer(w,&bw,PyBUF_C_CONTIGUOUS)<0) goto done;
    J->nwin=bw.len/8; PyBuffer_Release(&bw);
    J->win_starts=hmf_table_copy(w,J->nwin,8,0,&failed);
    if(failed) goto done;
    PyObject *mbs=PySequence_Fast(mb,"merge bin sizes must be a sequence");
    if(!mbs) goto done;
    J->nmerge=(int)PySequence_Fast_GET_SIZE(mbs);
    J->merge_bs=PyMem_Malloc((size_t)(J->nmerge?J->nmerge:1)*sizeof(Py_ssize_t));
    if(!J->merge_bs){ Py_DECREF(mbs); PyErr_NoMemory(); goto done; }
    for(int k=0;k<J->nmerge;k++){
      J->merge_bs[k]=PyNumber_AsSsize_t(PySequence_Fast_GET_ITEM(mbs,k),PyExc_OverflowError);
      if(J->merge_bs[k]<1){
        Py_DECREF(mbs);
        if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"HMFTable: a bin size below 1");
        goto done;
      }
    }
    Py_DECREF(mbs);
  }
  int last_phase=0;
  for(Py_ssize_t i=0;i<ns;i++){
    hmf_step *s=&self->steps[i];
    self->nsteps=(int)i+1;
    PyObject *st,*lo,*hi,*ph,*prices,*tmap,*order,*ost,*stats=Py_None; HMFObject *hmf;
    int nt; Py_ssize_t binsize; double thr;
    if(!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(steps,i),"O!iiiOOOOindOiiOOO|O",&HMFType,&hmf,
                         &s->slot,&s->real,&s->stride,&st,&lo,&hi,&ph,&nt,&binsize,&thr,&prices,
                         &s->phase,&s->job,&tmap,&order,&ost,&stats))
      goto done;
    if(stats!=Py_None){
      if(PyObject_GetBuffer(stats,&s->stats,PyBUF_C_CONTIGUOUS|PyBUF_WRITABLE)<0) goto done;
      s->has_stats=1;
      if(s->stats.len!=(6+256)*8){ PyErr_SetString(PyExc_ValueError,"HMFTable: a step's stats buffer has the wrong length"); goto done; }
    }
    Py_INCREF(hmf); s->hmf=hmf;
    if(s->slot<0 || s->slot>=nslots || s->job<0 || s->job>=self->njobs
       || s->stride<1 || s->stride>2 || (!s->real && s->stride!=1) || binsize<1
       || nt<1 || nt>hmf->nt || s->phase<-1 || (s->phase==-1 && !self->ops)
       || (s->phase>=0 && last_phase>s->phase)
       || (i && s->job<self->steps[i-1].job)){
      PyErr_SetString(PyExc_ValueError,"HMFTable: a step's slot, job, phase, mode or shape is invalid");
      goto done;
    }
    if(s->phase>=0) last_phase=s->phase;
    if(prices!=Py_None){
      if(!PyArg_ParseTuple(prices,"dd",&s->lagtap,&s->fftpair)) goto done;
      s->has_prices=1;
    }
    Py_buffer bst;
    if(PyObject_GetBuffer(st,&bst,PyBUF_C_CONTIGUOUS)<0) goto done;
    const Py_ssize_t nb=bst.len/(Py_ssize_t)sizeof(size_t);
    PyBuffer_Release(&bst);
    if(nb<1 || nb>INT_MAX){ PyErr_SetString(PyExc_ValueError,"HMFTable: a step needs blocks"); goto done; }
    int failed;
    s->nblocks=(int)nb; s->nt=nt; s->binsize=(size_t)binsize; s->threshold=(float)thr;
    s->block_len=(size_t)hmf->n;
    s->starts=hmf_table_copy(st,nb,sizeof(size_t),0,&failed); if(failed) goto done;
    s->low=hmf_table_copy(lo,nb,sizeof(size_t),0,&failed); if(failed) goto done;
    s->high=hmf_table_copy(hi,nb,sizeof(size_t),0,&failed); if(failed) goto done;
    s->bin_phase=hmf_table_copy(ph,nb,sizeof(unsigned),1,&failed); if(failed) goto done;
    s->tmap=hmf_table_copy(tmap,nt,8,0,&failed); if(failed) goto done;
    s->order=hmf_table_copy(order,nb,8,1,&failed); if(failed) goto done;
    s->ostarts=hmf_table_copy(ost,nb,8,0,&failed); if(failed) goto done;
    s->s_min=s->s_max=(int64_t)s->starts[0];
    for(int b=0;b<s->nblocks;b++){
      size_t bins; Py_ssize_t ignored;
      if(s->starts[b]>(size_t)INT64_MAX-(size_t)hmf->n || s->low[b]>(size_t)PY_SSIZE_T_MAX
         || s->high[b]>(size_t)PY_SSIZE_T_MAX){
        PyErr_SetString(PyExc_ValueError,"block offset or window overflows"); goto done;
      }
      if(!run_shape(hmf->n,1,hmf->nt,0,1,0,nt,binsize,(Py_ssize_t)s->low[b],
                    (Py_ssize_t)s->high[b],&bins,&ignored)) goto done;
      if(s->bin_phase){
        if(s->bin_phase[b]>=(1u<<24)){ PyErr_SetString(PyExc_ValueError,"bin_phase must be below 2**24"); goto done; }
        bins=ap_bin_count((size_t)binsize,s->low[b],s->high[b]>(size_t)hmf->n?(size_t)hmf->n:s->high[b],
                          s->bin_phase[b]);
      }
      if(b && bins!=s->nbins){ PyErr_SetString(PyExc_ValueError,"block windows must have equal bin counts"); goto done; }
      s->nbins=bins;
      if((int64_t)s->starts[b]<s->s_min) s->s_min=(int64_t)s->starts[b];
      if((int64_t)s->starts[b]>s->s_max) s->s_max=(int64_t)s->starts[b];
      if(s->order && (s->order[b]<0 || s->order[b]>=nb)){
        PyErr_SetString(PyExc_ValueError,"HMFTable: an output row is out of range"); goto done;
      }
    }
    for(int t=0;t<nt;t++) if(s->tmap[t]<0){ PyErr_SetString(PyExc_ValueError,"HMFTable: a negative template index"); goto done; }
  }
  /* the flat steps */
  if(flats_arg){
    flats=PySequence_Fast(flats_arg,"flats must be a sequence");
    if(!flats) goto done;
    const Py_ssize_t nf=PySequence_Fast_GET_SIZE(flats);
    if(nf>INT_MAX){ PyErr_SetString(PyExc_ValueError,"HMFTable: too many flat steps"); goto done; }
    self->flats=PyMem_Calloc(nf?(size_t)nf:1,sizeof(hmf_flat_step));
    if(!self->flats){ PyErr_NoMemory(); goto done; }
    for(Py_ssize_t i=0;i<nf;i++){
      hmf_flat_step *f=&self->flats[i];
      self->nflats=(int)i+1;
      PyObject *st,*lo,*hi,*ph,*tmap,*ost,*stats; MFObject *mf;
      int nt; Py_ssize_t binsize; double thr;
      if(!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(flats,i),"O!iiiOOOOindiOOO",&MFType,&mf,
                           &f->slot,&f->real,&f->stride,&st,&lo,&hi,&ph,&nt,&binsize,&thr,
                           &f->job,&tmap,&ost,&stats))
        goto done;
      Py_INCREF(mf); f->mf=mf;
      if(stats!=Py_None){
        if(PyObject_GetBuffer(stats,&f->stats,PyBUF_C_CONTIGUOUS|PyBUF_WRITABLE)<0) goto done;
        f->has_stats=1;
        if(f->stats.len!=(6+256)*8){ PyErr_SetString(PyExc_ValueError,"HMFTable: a step's stats buffer has the wrong length"); goto done; }
      }
      if(f->slot<0 || f->slot>=nslots || f->job<0 || f->job>=self->njobs
         || f->stride<1 || f->stride>2 || (!f->real && f->stride!=1) || binsize<1
         || nt<1 || nt>mf->nt || mf->nd!=1 || !(thr>=0.0)
         || (i && f->job<self->flats[i-1].job)){
        PyErr_SetString(PyExc_ValueError,"HMFTable: a flat step's slot, job, mode or shape is invalid");
        goto done;
      }
      Py_buffer bst;
      if(PyObject_GetBuffer(st,&bst,PyBUF_C_CONTIGUOUS)<0) goto done;
      const Py_ssize_t nb=bst.len/(Py_ssize_t)sizeof(size_t);
      PyBuffer_Release(&bst);
      if(nb<1 || nb>INT_MAX || nb>PY_SSIZE_T_MAX/nt){ PyErr_SetString(PyExc_ValueError,"HMFTable: a step needs blocks"); goto done; }
      int failed;
      f->nblocks=(int)nb; f->nt=nt; f->binsize=(size_t)binsize; f->threshold=(float)thr;
      f->block_len=(size_t)mf->n;
      f->starts=hmf_table_copy(st,nb,sizeof(size_t),0,&failed); if(failed) goto done;
      f->low=hmf_table_copy(lo,nb,sizeof(size_t),0,&failed); if(failed) goto done;
      f->high=hmf_table_copy(hi,nb,sizeof(size_t),0,&failed); if(failed) goto done;
      f->bin_phase=hmf_table_copy(ph,nb,sizeof(unsigned),1,&failed); if(failed) goto done;
      f->tmap=hmf_table_copy(tmap,nt,8,0,&failed); if(failed) goto done;
      f->ostarts=hmf_table_copy(ost,nb,8,0,&failed); if(failed) goto done;
      f->s_min=f->s_max=f->starts[0];
      /* each block's bin count, as run_series checks it */
      for(int b=0;b<f->nblocks;b++){
        size_t bins; Py_ssize_t ignored;
        if(f->starts[b]>(size_t)INT64_MAX-(size_t)mf->n || f->low[b]>(size_t)PY_SSIZE_T_MAX
           || f->high[b]>(size_t)PY_SSIZE_T_MAX){
          PyErr_SetString(PyExc_ValueError,"block offset or window overflows"); goto done;
        }
        if(!run_shape(mf->n,1,mf->nt,0,1,0,nt,binsize,(Py_ssize_t)f->low[b],
                      (Py_ssize_t)f->high[b],&bins,&ignored)) goto done;
        if(f->bin_phase){
          if(f->bin_phase[b]>=(1u<<24)){ PyErr_SetString(PyExc_ValueError,"bin_phase must be below 2**24"); goto done; }
          bins=ap_bin_count((size_t)binsize,f->low[b],f->high[b]>(size_t)mf->n?(size_t)mf->n:f->high[b],
                            f->bin_phase[b]);
        }
        if(b && bins!=f->nbins){ PyErr_SetString(PyExc_ValueError,"block windows must have equal bin counts"); goto done; }
        f->nbins=bins;
        if(f->starts[b]<f->s_min) f->s_min=f->starts[b];
        if(f->starts[b]>f->s_max) f->s_max=f->starts[b];
      }
      if(f->nbins<1 || f->nbins>(size_t)(PY_SSIZE_T_MAX/(Py_ssize_t)sizeof(ap_peak))/((size_t)nb*(size_t)nt)){
        PyErr_SetString(PyExc_ValueError,"invalid or overflowing output shape"); goto done;
      }
      for(int t=0;t<nt;t++) if(f->tmap[t]<0){ PyErr_SetString(PyExc_ValueError,"HMFTable: a negative template index"); goto done; }
    }
  }
  rc=0;
done:
  Py_DECREF(steps); Py_DECREF(jobs); Py_XDECREF(flats);
  if(rc) hmf_table_free_contents(self);
  return rc;
}
/* A slot's series as a step reads it: its first sample, its samples, and the bytes it spans
   (a lane of a complex series spans to its last sample's float). */
typedef struct { Py_buffer view; int held; const char *ptr; Py_ssize_t samples; int kind; } hmf_slot;
/* kind: 0 complex64, 1 contiguous float32, 2 float32 lane of a complex64 series (stride 8). */
static int hmf_slot_bind(PyObject *o,hmf_slot *sl){
  sl->held=0;
  if(PyObject_GetBuffer(o,&sl->view,PyBUF_STRIDES|PyBUF_FORMAT)<0) return -1;
  sl->held=1;
  const Py_buffer *v=&sl->view;
  const char *f=v->format?v->format:"B";
  if(*f=='<' || *f=='=' || *f=='@') f++;
  if(v->ndim!=1){ PyErr_SetString(PyExc_ValueError,"HMFTable: a series must be one-dimensional"); return -1; }
  sl->ptr=v->buf; sl->samples=v->shape[0];
  if(!strcmp(f,"Zf") && v->itemsize==8 && v->strides[0]==8) sl->kind=0;
  else if(!strcmp(f,"f") && v->itemsize==4 && v->strides[0]==4) sl->kind=1;
  else if(!strcmp(f,"f") && v->itemsize==4 && v->strides[0]==8) sl->kind=2;
  else { PyErr_SetString(PyExc_ValueError,"HMFTable: a series must be complex64, float32, or one "
                         "float32 lane of a complex64 series"); return -1; }
  return 0;
}
static int hmf_step_mode_ok(const hmf_step *s,const hmf_slot *sl){
  return s->real ? (sl->kind==(s->stride==2?2:1)) : sl->kind==0;
}
/* Set a step's plan to its series mode and prices, where it is in another (another call
   shape, or another table, ran it last). */
static int hmf_step_set_mode(hmf_step *s){
  HMFObject *h=s->hmf;
  if(h->real!=s->real || (s->real && h->real_stride!=s->stride)){
    if(ap_hmf_set_real_series(h->p,s->real) || ap_hmf_set_real_stride(h->p,(size_t)s->stride)){
      PyErr_SetString(PyExc_RuntimeError,"HMFTable: a plan refused its series mode"); return -1;
    }
    h->real=s->real; h->real_stride=s->stride;
  }
  if(s->has_prices){
    long pairs,lags,fft; double lt,fp;
    ap_hmf_direct_stats(h->p,&pairs,&lags,&fft,&lt,&fp);
    if(lt!=s->lagtap || fp!=s->fftpair) ap_hmf_set_direct_prices(h->p,s->lagtap,s->fftpair);
  }
  return 0;
}
static void hmf_job_bind(ap_hmf_sparse_job *jb,const hmf_step *s,const hmf_slot *sl,int b0,int b1,int cluster){
  memset(jb,0,sizeof(*jb));
  jb->p=s->hmf->p;
  jb->series=(const float*)sl->ptr;
  jb->nseries=(size_t)sl->samples;
  jb->start=s->starts+b0; jb->win_start=s->low+b0; jb->win_end=s->high+b0;
  jb->bin_phase=s->bin_phase?s->bin_phase+b0:NULL;
  jb->nblocks=b1-b0; jb->t0=0; jb->nt=s->nt;
  jb->binsize=s->binsize; jb->threshold=s->threshold; jb->counts=NULL; jb->cluster_id=cluster;
}
static double hmf_now(void){
  struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts);
  return (double)ts.tv_sec+1e-9*(double)ts.tv_nsec;
}
/* The bytes a step's blocks read of its series, widened to cache lines: the span the batch's
   Python caller computed to cluster steps that share cache lines. */
typedef struct { uintptr_t lo,hi; int idx; } hmf_span;
static int hmf_span_cmp(const void *a,const void *b){
  const hmf_span *x=a,*y=b;
  if(x->lo!=y->lo) return x->lo<y->lo?-1:1;
  if(x->hi!=y->hi) return x->hi<y->hi?-1:1;
  return x->idx<y->idx?-1:(x->idx>y->idx);
}
static int hmf_int_cmp(const void *a,const void *b){
  const int x=*(const int*)a,y=*(const int*)b; return (x>y)-(x<y);
}
typedef struct { int first; int *members; int count; } hmf_cluster;
static int hmf_cluster_cmp(const void *a,const void *b){
  const hmf_cluster *x=a,*y=b; return (x->first>y->first)-(x->first<y->first);
}
/* The window-bin merge of a job's peaks (time_domain._merge_window_bins with a float sample
   column, as the bank's assembly had it): kept indices in order into keep, their count
   returned; -2 on a peak before the first window. Peaks in template-then-sample order are
   compared by hypotf, as window_bin_keep compares them. Others are ordered as numpy's lexsort
   over -|v| orders them, the magnitude by hypotf, or, with numpy_magnitude, as np.abs of a
   complex64 computes it (the larger part times sqrt(1 + ratio^2), the square fused: numpy's
   complex absolute loop), which differs from hypotf in the last place for some values, and so
   decides between two peaks hypotf calls equal: the Python merge's comparison, which
   assemble_peaks keeps. HMFTable.run's steps keep hypotf, as they had it. */
typedef struct { int64_t t,w,b; float negm; double s; Py_ssize_t i; } hmf_mkey;
static int hmf_mkey_cmp(const void *a,const void *b){
  const hmf_mkey *x=a,*y=b;
  if(x->t!=y->t) return x->t<y->t?-1:1;
  if(x->w!=y->w) return x->w<y->w?-1:1;
  if(x->b!=y->b) return x->b<y->b?-1:1;
  if(x->negm!=y->negm) return x->negm<y->negm?-1:1;
  if(x->s!=y->s) return x->s<y->s?-1:1;
  return (x->i>y->i)-(x->i<y->i);
}
static int hmf_pidx_cmp(const void *a,const void *b){
  const Py_ssize_t x=*(const Py_ssize_t*)a,y=*(const Py_ssize_t*)b; return (x>y)-(x<y);
}
static Py_ssize_t hmf_merge_bins(const int64_t *W,Py_ssize_t nw,int64_t binsize,const int64_t *t,
                                 const double *s,const float *v,Py_ssize_t n,Py_ssize_t *keep,
                                 int numpy_magnitude){
  if(n<2){ for(Py_ssize_t i=0;i<n;i++) keep[i]=i; return n; }
  /* ordered by template then sample: adjacent runs (window_bin_keep) */
  int ordered=1;
  {
    Py_ssize_t w=0,kept=0,best=-1; float bestm=0.f; int64_t kt=0,kw=0,kb=0;
    for(Py_ssize_t i=0;i<n;i++){
      const double x=s[i];
      if(i>0 && (t[i]<t[i-1] || (t[i]==t[i-1] && s[i]<=s[i-1]))){ ordered=0; break; }
      if(i==0 || t[i]!=t[i-1]) w=0;
      while(w+1<nw && (double)W[w+1]<=x) w++;
      if(!(x>=(double)W[w])) return -2;
      const int64_t b=wbk_bin_f(x-(double)W[w],(double)binsize);
      const float m=hypotf(v[2*i],v[2*i+1]);
      if(i>0 && t[i]==kt && (int64_t)w==kw && b==kb){
        if(m>bestm){ bestm=m; best=i; }
        continue;
      }
      if(best>=0) keep[kept++]=best;
      kt=t[i]; kw=w; kb=b; best=i; bestm=m;
    }
    if(ordered){ if(best>=0) keep[kept++]=best; return kept; }
  }
  /* otherwise numpy's: lexsort((s, -|v|, bin, window, template)), the first of each
     (template, window, bin), kept in their original order */
  hmf_mkey *k=PyMem_Malloc((size_t)n*sizeof(hmf_mkey));
  if(!k) return -3;
  for(Py_ssize_t i=0;i<n;i++){
    Py_ssize_t lo=0,hi=nw;                 /* searchsorted(W, s, 'right') - 1 */
    while(lo<hi){ const Py_ssize_t mid=(lo+hi)/2; if((double)W[mid]<=s[i]) lo=mid+1; else hi=mid; }
    const Py_ssize_t wi=lo-1<0?nw-1:lo-1;  /* numpy's index -1 is the last window */
    k[i].t=t[i]; k[i].w=wi; k[i].b=wbk_bin_f(s[i]-(double)W[wi],(double)binsize);
    float m;
    if(numpy_magnitude){
      const float re=fabsf(v[2*i]), im=fabsf(v[2*i+1]);
      const float larger=re>im?re:im, smaller=re>im?im:re;
      if(isinf(re) || isinf(im)) m=INFINITY;
      else if(isnan(re) || isnan(im)) m=NAN;
      else if(larger==0.f) m=0.f;
      else { const float ratio=smaller/larger; m=sqrtf(fmaf(ratio,ratio,1.f))*larger; }
    } else m=hypotf(v[2*i],v[2*i+1]);
    k[i].negm=-m; k[i].s=s[i]; k[i].i=i;
  }
  qsort(k,(size_t)n,sizeof(hmf_mkey),hmf_mkey_cmp);
  Py_ssize_t kept=0;
  for(Py_ssize_t i=0;i<n;i++)
    if(i==0 || k[i].t!=k[i-1].t || k[i].w!=k[i-1].w || k[i].b!=k[i-1].b) keep[kept++]=k[i].i;
  PyMem_Free(k);
  qsort(keep,(size_t)kept,sizeof(Py_ssize_t),hmf_pidx_cmp);
  return kept;
}
typedef struct { int64_t key; Py_ssize_t i; } hmf_flat;
static int hmf_flat_cmp(const void *a,const void *b){
  const hmf_flat *x=a,*y=b;
  if(x->key!=y->key) return x->key<y->key?-1:1;
  return (x->i>y->i)-(x->i<y->i);
}
static PyObject *hmf_bytes(const void *src,Py_ssize_t nbytes){
  return PyBytes_FromStringAndSize(src?(const char*)src:"",src?nbytes:0);
}
/* The calls bound to a table's single-template steps, run together: per call its step, row
   (template), series, windows and the peaks the follow-up kernel kept. */
typedef struct {
  Py_ssize_t ncalls;
  int *single, *row;
  int64_t *offs;                 /* [ncalls + 1] into si, snr, bs */
  int64_t *si, *bs; float *snr;  /* malloc'd by td_followup_exec */
  size_t kept;
  double seconds;
  int few;                       /* single, row and offs are the few_ arrays below */
  int few_single[8], few_row[8];
  int64_t few_offs[9];
} hmf_single_out;
static void hmf_single_out_free(hmf_single_out *o){
  if(!o->few){ PyMem_Free(o->single); PyMem_Free(o->row); PyMem_Free(o->offs); }
  free(o->si);
  memset(o,0,sizeof(*o));
}
/* Bind each call (single, series, row, windows, binsize, aligned, threshold) to its step, give
   each template a spectrum (given; held in the group's store; or made in the scratch), and run
   every call with the follow-up kernel. 0, or -1 with the exception set. */
static int hmf_run_singles(HMFTableObject *self,PyObject *calls_arg,hmf_single_out *out){
  memset(out,0,sizeof(*out));
  PyObject *calls=PySequence_Fast(calls_arg,"calls must be a sequence");
  if(!calls) return -1;
  const Py_ssize_t nc=PySequence_Fast_GET_SIZE(calls);
  out->ncalls=nc;
  int rc=-1;
  hmf_slot *views=NULL; Py_buffer *wins=NULL; char *wheld=NULL; int *slot=NULL, *busy=NULL;
  int64_t *clock0=NULL;
  TdBatchScratch *ws=NULL;
  /* per call: its step and row, offsets (out), its series and windows views, its store slot;
     per step: whether this run holds its store, and the store's clock when it took it. A
     run of a few calls on a few steps (a follow-up's) keeps these on the stack. */
  enum { HMF_FEW=8 };
  int few_slot[HMF_FEW], few_busy[HMF_FEW];
  int64_t few_clock[HMF_FEW];
  hmf_slot few_views[HMF_FEW]; Py_buffer few_wins[HMF_FEW]; char few_wheld[HMF_FEW];
  const size_t cnt=nc?(size_t)nc:1, ng=self->nsingles?(size_t)self->nsingles:1;
  out->few=cnt<=HMF_FEW;
  if(out->few){
    out->single=out->few_single; out->row=out->few_row; out->offs=out->few_offs;
    memset(out->few_offs,0,sizeof(out->few_offs));
    views=few_views; wins=few_wins;
    wheld=few_wheld; slot=few_slot;
    memset(few_views,0,sizeof(few_views)); memset(few_wheld,0,sizeof(few_wheld));
  } else {
    out->single=PyMem_Calloc(cnt,sizeof(int)); out->row=PyMem_Calloc(cnt,sizeof(int));
    out->offs=PyMem_Calloc(cnt+1,sizeof(int64_t));
    views=PyMem_Calloc(cnt,sizeof(hmf_slot)); wins=PyMem_Calloc(cnt,sizeof(Py_buffer));
    wheld=PyMem_Calloc(cnt,1); slot=PyMem_Calloc(cnt,sizeof(int));
  }
  if(ng<=HMF_FEW){
    busy=few_busy; clock0=few_clock; memset(few_busy,0,sizeof(few_busy));
  } else {
    busy=PyMem_Calloc(ng,sizeof(int)); clock0=PyMem_Calloc(ng,sizeof(int64_t));
  }
  if(!out->single||!out->row||!out->offs||!views||!wins||!wheld||!slot||!busy||!clock0){ PyErr_NoMemory(); goto done; }
  if(!nc){ rc=0; goto done; }
  ws=td_bscr_acquire();
  if(!ws){ PyErr_NoMemory(); goto done; }
  if(td_grow_raw((void**)&ws->jobs,&ws->jobs_cap,(size_t)nc,sizeof(TdJob))<0){ PyErr_NoMemory(); goto done; }
  TdJob *jobs=ws->jobs;
  memset(jobs,0,(size_t)nc*sizeof(TdJob));
  /* each call's step, series, windows and template */
  for(Py_ssize_t c=0;c<nc;c++){
    int si,aligned; Py_ssize_t row,binsize; PyObject *ser,*win; float thr;
    if(!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(calls,c),"iOnOnpf",&si,&ser,&row,&win,&binsize,
                         &aligned,&thr)) goto done;
    if(si<0 || si>=self->nsingles || row<0 || row>=self->singles[si].nt || binsize<1){
      PyErr_SetString(PyExc_ValueError,"HMFTable.run: a call's step, template or bin size is out of range");
      goto done;
    }
    const hmf_single *g=&self->singles[si];
    out->single[c]=si; out->row[c]=(int)row; slot[c]=-1;
    if(hmf_slot_bind(ser,&views[c])) goto done;
    TdJob *jb=&jobs[c];
    const hmf_slot *sv=&views[c];
    jb->ser_f=(const float*)sv->ptr; jb->s_kind=sv->kind; jb->S=(int64_t)sv->samples;
    jb->cser_floats=sv->kind==2?(sv->samples>0?(size_t)(2*sv->samples-1):0u)
                   :(size_t)sv->samples*(sv->kind==0?2u:1u);
    if(PyTuple_CheckExact(win) && PyTuple_GET_SIZE(win)==2){
      const long long v0=PyLong_AsLongLong(PyTuple_GET_ITEM(win,0));
      const long long v1=PyLong_AsLongLong(PyTuple_GET_ITEM(win,1));
      if(PyErr_Occurred()) goto done;
      jb->single_w[0]=(int64_t)v0; jb->single_w[1]=(int64_t)v1;
      jb->W=jb->single_w; jb->nw=(v0<v1)?1u:0u;
    } else {
      if(PyObject_GetBuffer(win,&wins[c],PyBUF_C_CONTIGUOUS)<0) goto done;
      wheld[c]=1;
      if(wins[c].len%(2*(Py_ssize_t)sizeof(int64_t))){
        PyErr_SetString(PyExc_ValueError,"HMFTable.run: windows must be (K, 2) int64"); goto done;
      }
      jb->W=(const int64_t*)wins[c].buf; jb->nw=(size_t)(wins[c].len/(2*(Py_ssize_t)sizeof(int64_t)));
    }
    jb->n=g->n; jb->step=g->step; jb->c_bad=g->c_bad; jb->bs=(size_t)binsize;
    jb->aligned=aligned?1:0; jb->thr=thr; memcpy(&jb->thr_bits,&thr,sizeof(uint32_t));
    jb->global_ti=g->tmap[row];
    const int64_t given=(g->held&8)?((const int64_t*)g->spectrum_rows.buf)[row]:-1;
    if(given>=0){
      jb->spec=(float*)g->spectra.buf+(size_t)given*2*g->n; jb->spec_ready=1;
    } else {
      jb->rate_one=1; jb->L=(int)((const int64_t*)g->counts.buf)[row]; jb->tr_cplx=g->tr_cplx;
      jb->tr=(const float*)g->taps.buf+(size_t)row*(size_t)g->row_floats;
    }
  }
  /* the spectra made from taps: a slot of the group's store (least recently used first; a
     store another run holds is not used), or the scratch; a template given twice is one
     spectrum, as the kernel shares it */
  size_t nmade=0;
  for(Py_ssize_t c=0;c<nc;c++){
    TdJob *jb=&jobs[c];
    if(!jb->rate_one) continue;
    const int si=out->single[c], row=out->row[c];
    Py_ssize_t twin=-1;
    for(Py_ssize_t p=0;p<c;p++) if(jobs[p].rate_one && out->single[p]==si && out->row[p]==row){ twin=p; break; }
    if(twin>=0){ slot[c]=slot[twin]; jb->spec=jobs[twin].spec; jb->spec_ready=jobs[twin].spec_ready; continue; }
    SpectrumStoreObject *st=self->singles[si].store;
    if(!busy[si]){
      if(st->busy){ busy[si]=-1; }                    /* another run holds the store */
      else { st->busy=1; busy[si]=1; clock0[si]=st->clock; }
    }
    if(busy[si]<0){ slot[c]=-1; nmade++; continue; }
    int k=-1;
    for(int q=0;q<st->nalloc;q++) if(st->row_of[q]==row){ k=q; break; }
    if(k<0){
      if(st->nalloc<st->cap){
        /* a new slot, allocated now */
        float *buf=(float*)ap_alloc64(2*st->n*sizeof(float));
        if(!buf){ PyErr_NoMemory(); goto done; }
        k=st->nalloc++; st->spec[k]=buf;
      } else {
        int best=0;
        for(int q=1;q<st->cap;q++) if(st->used[q]<st->used[best]) best=q;
        if(st->used[best]>clock0[si]){ slot[c]=-1; nmade++; continue; }   /* every slot serves this run */
        k=best;
      }
      st->row_of[k]=row; st->ready[k]=0;
    }
    st->used[k]=++st->clock;
    slot[c]=k;
    jb->spec=st->spec[k]; jb->spec_ready=(int)st->ready[k];
  }
  if(nmade){
    size_t nmax=0;
    for(Py_ssize_t c=0;c<nc;c++) if(jobs[c].rate_one && slot[c]<0 && jobs[c].n>nmax) nmax=jobs[c].n;
    float *made=td_bscr_spectra(ws,nmade,nmax);
    if(!made){ PyErr_NoMemory(); goto done; }
    size_t m=0;
    for(Py_ssize_t c=0;c<nc;c++){
      if(!jobs[c].rate_one || slot[c]>=0 || jobs[c].spec) continue;
      jobs[c].spec=made+m*2*nmax; m++;
      for(Py_ssize_t q=c+1;q<nc;q++)
        if(jobs[q].rate_one && slot[q]<0 && !jobs[q].spec && out->single[q]==out->single[c]
           && out->row[q]==out->row[c]) jobs[q].spec=jobs[c].spec;
    }
  }
  /* the kernel */
  int err;
  const double t0=hmf_now();
  Py_BEGIN_ALLOW_THREADS
  err=td_followup_exec(ws,jobs,(size_t)nc,out->offs,&out->si,&out->snr,&out->bs,&out->kept);
  Py_END_ALLOW_THREADS
  out->seconds=hmf_now()-t0;
  if(err){ PyErr_SetString(PyExc_RuntimeError,"HMFTable.run: the follow-up kernel failed"); goto done; }
  /* a slot whose spectrum the kernel made now holds it */
  for(Py_ssize_t c=0;c<nc;c++){
    if(slot[c]<0 || !jobs[c].spec_ready) continue;
    self->singles[out->single[c]].store->ready[slot[c]]=1;
  }
  rc=0;
done:
  if(busy) for(int i=0;i<self->nsingles;i++)
    if(busy[i]>0) self->singles[i].store->busy=0;
  if(views) for(Py_ssize_t c=0;c<nc;c++) if(views[c].held) PyBuffer_Release(&views[c].view);
  if(wins) for(Py_ssize_t c=0;c<nc;c++) if(wheld[c]) PyBuffer_Release(&wins[c]);
  if(ws) td_bscr_release(ws);
  if(cnt>HMF_FEW){ PyMem_Free(views); PyMem_Free(wins); PyMem_Free(wheld); PyMem_Free(slot); }
  if(ng>HMF_FEW){ PyMem_Free(busy); PyMem_Free(clock0); }
  Py_DECREF(calls);
  if(rc) hmf_single_out_free(out);
  return rc;
}
/* run(series, calls=()) -> (offsets, templates, samples, snr, block_starts, block_lengths,
   step totals, step seconds, kernel seconds): series one per slot of the gated steps; calls
   (single, series, row, windows, binsize, aligned, threshold) bound to the single-template
   steps, each a job after the table's own. The correlation steps run with run_corr. */
/* Append one step's m peaks (flat (block, template, bin) index, lag and value each, blocks in
   computed order, order mapping a computed block to its output row or NULL) to the arena at
   at, in output order: block-major, then template, then bin. Returns the new end, or -1 with
   MemoryError set. */
static Py_ssize_t hmf_append_peaks(int64_t *o_t,double *o_s,float *o_v,int64_t *o_bs,int64_t *o_bl,
                                   Py_ssize_t at,const int64_t *tmap,const int64_t *ostarts,
                                   const int64_t *order,int64_t nt,int64_t nbins,size_t block_len,
                                   Py_ssize_t m,const int64_t *flat,const int64_t *idx,
                                   const float *val){
  const int64_t per_block=nt*nbins;
  hmf_flat *ord=NULL;
  if(order){
    ord=PyMem_Malloc((size_t)m*sizeof(hmf_flat));
    if(!ord){ PyErr_NoMemory(); return -1; }
    for(Py_ssize_t q=0;q<m;q++){
      const int64_t f=flat[q];
      ord[q].key=order[f/per_block]*per_block+f%per_block; ord[q].i=q;
    }
    qsort(ord,(size_t)m,sizeof(hmf_flat),hmf_flat_cmp);
  }
  for(Py_ssize_t q=0;q<m;q++){
    const Py_ssize_t src=ord?ord[q].i:q;
    const int64_t f=ord?ord[q].key:flat[src];
    const int64_t bi=f/per_block, rest=f%per_block;
    o_t[at]=tmap[rest/nbins];
    o_bs[at]=ostarts[bi];
    o_s[at]=(double)ostarts[bi]+(double)idx[src];
    o_v[2*at]=val[2*src]; o_v[2*at+1]=val[2*src+1];
    o_bl[at]=(int64_t)block_len;
    at++;
  }
  PyMem_Free(ord);
  return at;
}
/* Run one flat step on its slot's series: a complex series in place, a real one (or a real lane
   of a complex one) widened to complex over the samples its blocks read, as filter_series did
   for a plan that does not read a real series. Its non-empty bins go to out in (block,
   template, bin) order. 0, or -1 with the exception set. Called without the GIL for the
   kernel: the plan is marked busy by the caller. */
static int hmf_run_flat(hmf_flat_step *f,const hmf_slot *sl,hmf_flat_out *out,double *seconds){
  memset(out,0,sizeof(*out));
  MFObject *mf=f->mf;
  const Py_ssize_t rows=(Py_ssize_t)f->nblocks*f->nt, need=rows*(Py_ssize_t)f->nbins;
  ap_peak *pk=reserve_peaks(&mf->peaks,&mf->peak_capacity,need);
  if(!pk) return -1;
  int *cnt=PyMem_Malloc((size_t)rows*sizeof(int));
  size_t *starts=NULL; float *wide=NULL;
  const float *ser=(const float*)sl->ptr; size_t nseries=(size_t)sl->samples;
  const size_t *st=f->starts;
  int rc=-1;
  if(!cnt){ PyErr_NoMemory(); goto done; }
  if(sl->kind){
    /* the span [lo, hi) the blocks read, as complex; the starts relative to it */
    const size_t lo=f->s_min;
    const size_t hi=f->s_max+f->block_len<(size_t)sl->samples?f->s_max+f->block_len:(size_t)sl->samples;
    const size_t len=hi>lo?hi-lo:0, step=sl->kind==2?2:1;
    wide=aligned_alloc(64,((len?len:1)*2*sizeof(float)+63)&~(size_t)63);
    starts=PyMem_Malloc((size_t)f->nblocks*sizeof(size_t));
    if(!wide||!starts){ PyErr_NoMemory(); goto done; }
    const float *x=(const float*)sl->ptr;
    for(size_t k=0;k<len;k++){ wide[2*k]=x[(lo+k)*step]; wide[2*k+1]=0.f; }
    for(int b=0;b<f->nblocks;b++) starts[b]=f->starts[b]-lo;
    ser=wide; nseries=len; st=starts;
  }
  int tot;
  const double t0=hmf_now();
  Py_BEGIN_ALLOW_THREADS
  tot=ap_mf_run_series(mf->p,ser,nseries,st,f->low,f->high,f->bin_phase,f->nblocks,0,f->nt,
                       f->binsize,f->threshold,pk,cnt);
  Py_END_ALLOW_THREADS
  *seconds=hmf_now()-t0;
  if(tot<0){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done; }
  out->total=tot;
  if(tot){
    size_t m=0;
    for(Py_ssize_t q=0;q<need;q++) m+=pk[q].index>=0;
    out->flat=malloc((m?m:1)*sizeof(int64_t)); out->idx=malloc((m?m:1)*sizeof(int64_t));
    out->val=malloc((m?m:1)*2*sizeof(float));
    if(!out->flat||!out->idx||!out->val){ PyErr_NoMemory(); goto done; }
    size_t k=0;
    for(Py_ssize_t q=0;q<need;q++) if(pk[q].index>=0){
      out->flat[k]=(int64_t)q; out->idx[k]=(int64_t)pk[q].index;
      out->val[2*k]=pk[q].re; out->val[2*k+1]=pk[q].im; k++;
    }
    out->count=m;
  }
  rc=0;
done:
  PyMem_Free(cnt); PyMem_Free(starts); free(wide);
  return rc;
}
void ap_mf_stream_copy(float *dst, const float *src, size_t bytes);
void ap_mf_stream_fence(void);
/* An output slot of the correlation steps: a C-contiguous writable complex64 array of one or
   two dimensions, as rows of `width` samples. */
typedef struct { Py_buffer view; int held; float *ptr; Py_ssize_t rows, width; } hmf_out_slot;
static int hmf_out_bind(PyObject *o,hmf_out_slot *sl){
  sl->held=0;
  if(PyObject_GetBuffer(o,&sl->view,PyBUF_C_CONTIGUOUS|PyBUF_WRITABLE|PyBUF_FORMAT)<0) return -1;
  sl->held=1;
  const Py_buffer *v=&sl->view;
  const char *f=v->format?v->format:"B";
  if(*f=='<' || *f=='=' || *f=='@') f++;
  if(strcmp(f,"Zf") || v->itemsize!=8 || v->ndim<1 || v->ndim>2){
    PyErr_SetString(PyExc_ValueError,"HMFTable: a correlation output must be a C-contiguous "
                    "writable complex64 array of one or two dimensions");
    return -1;
  }
  sl->ptr=v->buf;
  sl->rows=v->ndim==2?v->shape[0]:1; sl->width=v->shape[v->ndim-1];
  return 0;
}
/* Scale count complex samples by s: numpy's product of a complex64 array and a float32 scale
   (the scale as s + 0i), as the Python path computed it on the CPU (np.multiply): the real
   part re * s - im * 0 rounded once, the imaginary part re * 0 + im * s. Not contracted. */
#if defined(__GNUC__) && !defined(__clang__)
__attribute__((optimize("fp-contract=off")))
#endif
static void hmf_scale_run(float *z,size_t count,float s){
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
  const float zero=0.0f;
  for(size_t i=0;i<count;i++){
    const float re=z[2*i], im=z[2*i+1];
    z[2*i]=fmaf(re,s,-(im*zero));
    z[2*i+1]=re*zero+im*s;
  }
}
/* Correlation steps [c0, c1) on bound slots, outputs and scale vectors (nsc of them): every
   step's slots, rows and runs are checked first; then the kernels, the clearing and the
   scaling run in step order without the GIL, each step's plan marked busy, with the steps'
   mirrors where use_mirror. Their seconds go to *seconds. 0, or -1 with the exception set. */
static int hmf_corrs_exec(HMFTableObject *self,int c0,int c1,const hmf_slot *slots,
                          const hmf_out_slot *oslots,const Py_buffer *svec,Py_ssize_t nsc,
                          double *seconds){
  int err=0;
  /* every step's slots, rows and runs, before anything runs */
  for(int i=c0;i<c1;i++){
    const hmf_corr_step *c=&self->corrs[i];
    const hmf_slot *in=&slots[c->slot]; const hmf_out_slot *o=&oslots[c->out];
    const Py_ssize_t S=in->samples;
    int ok=(c->real ? in->kind==1 : in->kind==0) && o->width==S && S>0;
    if(ok && c->rows){ for(int t=0;t<c->nt;t++) if(c->rows[t]>=o->rows) ok=0; }
    else if(ok) ok=c->row0<=o->rows-c->nt;
    for(Py_ssize_t k=0;ok && k<c->nclear;k++) ok=c->clear[2*k+1]<=S;
    if(ok && c->scale>=0){
      ok=c->scale<nsc;
      for(int t=0;ok && t<c->nt;t++) ok=c->scale_index[t]<svec[c->scale].len/4;
      for(Py_ssize_t k=0;ok && k<c->nscale_runs;k++) ok=c->scale_runs[2*k+1]<=S;
    }
    if(!ok){
      PyErr_SetString(PyExc_ValueError,"HMFTable: a correlation step's series, output, rows or "
                      "scales do not fit what it was compiled for");
      return -1;
    }
    if(c->mf->busy){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter in use by another thread; use one filter per thread"); return -1; }
  }
  for(int i=c0;i<c1;i++) self->corrs[i].mf->busy=1;
  const double t0=hmf_now();
  Py_BEGIN_ALLOW_THREADS
  for(int i=c0;i<c1 && !err;i++){
    const hmf_corr_step *c=&self->corrs[i];
    const hmf_slot *in=&slots[c->slot]; const hmf_out_slot *o=&oslots[c->out];
    const size_t S=(size_t)in->samples, row=2*S;
    float *scratch=NULL, *dest=o->ptr+(size_t)c->row0*row;
    if(c->rows){
      scratch=ap_alloc64((size_t)c->nt*row*sizeof(float));
      if(!scratch){ err=2; break; }
      dest=scratch;
    }
    if(c->nblocks){
      const int r=c->real
        ? ap_mf_correlate_series_continuous_real(c->mf->p,(const float*)in->ptr,S,c->starts,
                                                 c->nblocks,c->lo,c->hi,c->t0,c->nt,dest,c->bounds)
        : ap_mf_correlate_series_continuous(c->mf->p,(const float*)in->ptr,S,c->starts,
                                            c->nblocks,c->lo,c->hi,c->t0,c->nt,dest,c->bounds);
      if(r) err=1;
    }
    if(!err){
      for(int t=0;t<c->nt;t++){
        float *z=dest+(size_t)t*row;
        for(Py_ssize_t k=0;k<c->nclear;k++){
          const int64_t a=c->clear[2*k], b=c->clear[2*k+1];
          if(b>a) memset(z+2*a,0,(size_t)(b-a)*2*sizeof(float));
        }
        if(c->scale>=0){
          const float s=((const float*)svec[c->scale].buf)[c->scale_index[t]];
          for(Py_ssize_t k=0;k<c->nscale_runs;k++){
            const int64_t a=c->scale_runs[2*k], b=c->scale_runs[2*k+1];
            if(b>a) hmf_scale_run(z+2*a,(size_t)(b-a),s);
          }
        }
        if(c->rows) memcpy(o->ptr+(size_t)c->rows[t]*row,z,row*sizeof(float));
      }
    }
    free(scratch);
  }
  Py_END_ALLOW_THREADS
  *seconds=hmf_now()-t0;
  for(int i=c0;i<c1;i++) self->corrs[i].mf->busy=0;
  if(err==2){ PyErr_NoMemory(); return -1; }
  if(err){ PyErr_SetString(PyExc_RuntimeError,"continuous series correlation failed"); return -1; }
  return 0;
}
/* Run correlation steps [c0, c1) on the series, outputs and scale vectors given (sequences;
   scales may be NULL), with their mirrors where use_mirror. Every step's slots, rows and runs
   are checked first; then the kernels, the clearing and the scaling run in step order without
   the GIL, each step's plan marked busy. The seconds of that part go to *seconds. 0, or -1
   with the exception set. */
static int hmf_run_corrs(HMFTableObject *self,int c0,int c1,PyObject *series_arg,PyObject *outs_arg,
                         PyObject *scales_arg,double *seconds){
  *seconds=0.0;
  if(c0>=c1) return 0;
  PyObject *ins=NULL,*outs=NULL,*scs=NULL;
  hmf_slot *slots=NULL; hmf_out_slot *oslots=NULL; Py_buffer *svec=NULL;
  Py_ssize_t nin=0,nout=0,nsc=0;
  int rc=-1;
  ins=PySequence_Fast(series_arg,"series must be a sequence");
  if(!ins) goto done;
  outs=PySequence_Fast(outs_arg,"outputs must be a sequence");
  if(!outs) goto done;
  nin=PySequence_Fast_GET_SIZE(ins); nout=PySequence_Fast_GET_SIZE(outs);
  if(nin!=self->nslots || nout!=self->nouts){
    PyErr_SetString(PyExc_ValueError,"HMFTable: one series per slot and one array per output slot");
    nin=nout=0; goto done;
  }
  slots=PyMem_Calloc(nin?(size_t)nin:1,sizeof(hmf_slot));
  oslots=PyMem_Calloc(nout?(size_t)nout:1,sizeof(hmf_out_slot));
  if(!slots||!oslots){ PyErr_NoMemory(); nin=nout=0; goto done; }
  for(Py_ssize_t k=0;k<nin;k++) if(hmf_slot_bind(PySequence_Fast_GET_ITEM(ins,k),&slots[k])) goto done;
  for(Py_ssize_t k=0;k<nout;k++) if(hmf_out_bind(PySequence_Fast_GET_ITEM(outs,k),&oslots[k])) goto done;
  if(scales_arg && scales_arg!=Py_None){
    scs=PySequence_Fast(scales_arg,"scales must be a sequence");
    if(!scs) goto done;
    const Py_ssize_t n=PySequence_Fast_GET_SIZE(scs);
    svec=PyMem_Calloc(n?(size_t)n:1,sizeof(Py_buffer));
    if(!svec){ PyErr_NoMemory(); goto done; }
    for(Py_ssize_t k=0;k<n;k++){
      if(PyObject_GetBuffer(PySequence_Fast_GET_ITEM(scs,k),&svec[k],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) goto done;
      nsc=k+1;
      const char *f=svec[k].format?svec[k].format:"B";
      if(*f=='<' || *f=='=' || *f=='@') f++;
      if(strcmp(f,"f") || svec[k].itemsize!=4){
        PyErr_SetString(PyExc_ValueError,"HMFTable: scales must be float32"); goto done;
      }
    }
  }
  if(hmf_corrs_exec(self,c0,c1,slots,oslots,svec,nsc,seconds)) goto done;
  rc=0;
done:
  if(slots) for(Py_ssize_t k=0;k<nin;k++) if(slots[k].held) PyBuffer_Release(&slots[k].view);
  if(oslots) for(Py_ssize_t k=0;k<nout;k++) if(oslots[k].held) PyBuffer_Release(&oslots[k].view);
  if(svec) for(Py_ssize_t k=0;k<nsc;k++) PyBuffer_Release(&svec[k]);
  PyMem_Free(slots); PyMem_Free(oslots); PyMem_Free(svec);
  Py_XDECREF(ins); Py_XDECREF(outs); Py_XDECREF(scs);
  return rc;
}
/* The schedule of a table: an order of its steps with buffer roles, run by hmf_run_schedule.
   The tiled middle-to-leaf schedule (a cohort of a middle bank's correlations and the leaf
   steps that read them, per time tile) is built from these ops, and so is a search chunk whose
   inner nodes have inner children (correlation step ranges with the lane copies between them
   that a child's real series needs); a table without a schedule runs every correlation step,
   then its leaf phases. A schedule's leaf steps (phase -1) run
   in block ranges (OP_LEAF) and their peaks are gathered per step (hmf_parts), assembled as
   one step's at the end. Ops: */
enum {
  HMF_OP_CORR=1,     /* c0, c1: correlation steps [c0, c1) */
  HMF_OP_POOL=3,     /* state, S, stride, pool, need: a scratch pool's layout; zeroed when
                        it changes (the pool's [0, need) and every dirty span) */
  HMF_OP_STALE=4,    /* state, D, rows, runs off, runs n, new lo, new hi, first scratch slot:
                        zero each scratch row's dirty span within the runs, then set it */
  HMF_OP_ZERO=5,     /* out slot, rows off, rows n, runs off, runs n */
  HMF_OP_SCALE=6,    /* out slot, rows off, rows n, runs off, runs n, scale vector, entries off */
  HMF_OP_COPY=7,     /* src slot, src row, dst slot, dst row, runs off, runs n, stream */
  HMF_OP_COLLAR=8,   /* restore, scratch slot, carry tile, carry offset, rows, lo, hi */
  HMF_OP_LEAF=9,     /* items off, items n, retain, retain threshold (double bits): items
                        (step, b0, b1, cluster, row) as one batch */
  HMF_OP_RETAIN=10,  /* header off: copies around the last OP_LEAF's peaks */
  HMF_OP_PENDING=11, /* n: the rows' pending retain ends, zeroed */
  HMF_OP_LANE=12     /* src slot, src row, part, dst series slot, runs off, runs n: within the
                        runs, part 0 (real) or 1 (imaginary) of an output row into a writable
                        contiguous float32 series that a later correlation step reads: a lane
                        of a packed pair, or (part 0) a real filter's output where its batch
                        writes complex rows, as _InnerBatch.prepare takes .real */
};
typedef struct { Py_buffer view; int held; char *ptr; Py_ssize_t len; } hmf_tile;
typedef struct {
  int64_t *flat, *idx; float *val; size_t count, cap;
  int64_t last_b0; int monotone, any, total; double seconds;
} hmf_parts;
typedef struct { int64_t *pos; size_t n, cap; } hmf_posv;
static int hmf_grow(void **p,size_t *cap,size_t need,size_t item){
  if(need<=*cap) return 0;
  size_t c=*cap?*cap:64; while(c<need) c*=2;
  void *q=realloc(*p,c*item); if(!q) return -1;
  *p=q; *cap=c; return 0;
}
static int hmf_parts_add(hmf_parts *pt,int64_t b0,int64_t per_block,const ap_hmf_sparse_job *jb){
  const size_t m=jb->out_count, need=pt->count+m;
  if(m){
    size_t c1=pt->cap,c2=pt->cap,c3=pt->cap;
    if(hmf_grow((void**)&pt->flat,&c1,need,8) || hmf_grow((void**)&pt->idx,&c2,need,8)
       || hmf_grow((void**)&pt->val,&c3,need,8)) return -1;
    pt->cap=c1;
    for(size_t q=0;q<m;q++){
      pt->flat[pt->count+q]=jb->out_flat[q]+b0*per_block; pt->idx[pt->count+q]=jb->out_idx[q];
      pt->val[2*(pt->count+q)]=jb->out_val[2*q]; pt->val[2*(pt->count+q)+1]=jb->out_val[2*q+1];
    }
    pt->count=need;
  }
  if(pt->any && b0<=pt->last_b0) pt->monotone=0;
  pt->any=1; pt->last_b0=b0;
  return 0;
}
#define HMF_RANGE_OK(off,n,w) ((off)>=0 && (n)>=0 && (off)+(Py_ssize_t)(w)*(n)<=self->nsargs)
static int hmf_runs_fit(const int64_t *r,int64_t n,Py_ssize_t S){
  for(int64_t k=0;k<n;k++) if(r[2*k]<0 || r[2*k+1]>S) return 0;
  return 1;
}
/* Run the table's schedule on bound slots, outputs, scale vectors and tiles. The correlation
   seconds (every op but OP_LEAF) go to *corr_seconds and the leaf kernels' to *leaf_seconds;
   each schedule step's peaks to parts. 0, or -1 with the exception set. */
static int hmf_run_schedule(HMFTableObject *self,const hmf_slot *slots,const hmf_out_slot *oslots,
                            int nouts,const Py_buffer *svec,Py_ssize_t nsc,const hmf_tile *tiles,
                            int ntiles,hmf_parts *parts,double *corr_seconds,double *leaf_seconds){
  int rc=-1, streamed=0;
  ap_hmf_sparse_job *jobs=NULL; size_t jcap=0;
  hmf_posv *pos=NULL; int npos=0;
  int64_t *pending=NULL; int64_t npending=0;
  int64_t *spans=NULL; size_t scap=0;
  const char *bad="HMFTable.run: a schedule op does not fit the buffers bound";
#define HMF_BAD() do{ PyErr_SetString(PyExc_ValueError,bad); goto done; }while(0)
  for(int o=0;o<self->nops;o++){
    const int64_t *f=self->ops+(size_t)o*HMF_OP_FIELDS;
    const double t0=hmf_now();
    switch((int)f[0]){
    case HMF_OP_CORR: {
      double dt=0.0;
      if(f[1]<0 || f[2]<f[1] || f[2]>self->ncorrs) HMF_BAD();
      if(hmf_corrs_exec(self,(int)f[1],(int)f[2],slots,oslots,svec,nsc,&dt)) goto done;
      break;
    }
    case HMF_OP_POOL: {
      if(f[1]<0 || f[1]>=ntiles || f[4]<0 || f[4]>=ntiles) HMF_BAD();
      int64_t *st=(int64_t*)tiles[f[1]].ptr;
      if(tiles[f[1]].len<16 || f[5]<0 || f[5]*8>tiles[f[4]].len) HMF_BAD();
      if(st[0]!=f[2] || st[1]!=f[3]){
        memset(tiles[f[4]].ptr,0,(size_t)f[5]*8);
        memset(st+2,0,(size_t)tiles[f[1]].len-16);
        st[0]=f[2]; st[1]=f[3];
      }
      break;
    }
    case HMF_OP_STALE: {
      if(f[1]<0 || f[1]>=ntiles || !HMF_RANGE_OK(f[4],f[5],2) || f[8]<0 || f[8]+f[2]>nouts
         || f[3]<0 || f[3]>8) HMF_BAD();
      int64_t *st=(int64_t*)tiles[f[1]].ptr;
      if(tiles[f[1]].len<(Py_ssize_t)(16+16*8*f[2])) HMF_BAD();
      const int64_t *runs=self->sargs+f[4];
      for(int64_t d=0;d<f[2];d++){
        const hmf_out_slot *sc=&oslots[f[8]+d];
        if(sc->rows<f[3] || !hmf_runs_fit(runs,f[5],sc->width)) HMF_BAD();
        for(int64_t q=0;q<f[3];q++){
          int64_t *dirty=st+2+2*(d*8+q);
          if(dirty[1]>dirty[0]){
            for(int64_t k=0;k<f[5];k++){
              const int64_t a=runs[2*k]>dirty[0]?runs[2*k]:dirty[0];
              const int64_t b=runs[2*k+1]<dirty[1]?runs[2*k+1]:dirty[1];
              if(b>a && a>=0 && b<=sc->width)
                memset(sc->ptr+((size_t)q*(size_t)sc->width+(size_t)a)*2,0,(size_t)(b-a)*8);
            }
          }
          dirty[0]=f[6]; dirty[1]=f[7];
        }
      }
      break;
    }
    case HMF_OP_ZERO: case HMF_OP_SCALE: {
      if(f[1]<0 || f[1]>=nouts || !HMF_RANGE_OK(f[2],f[3],1) || !HMF_RANGE_OK(f[4],f[5],2)) HMF_BAD();
      const hmf_out_slot *ou=&oslots[f[1]];
      const int64_t *rows=self->sargs+f[2], *runs=self->sargs+f[4];
      const float *sv=NULL;
      if(f[0]==HMF_OP_SCALE){
        if(f[6]<0 || f[6]>=nsc || !HMF_RANGE_OK(f[7],f[3],1)) HMF_BAD();
        sv=svec[f[6]].buf;
        for(int64_t r=0;r<f[3];r++)
          if(self->sargs[f[7]+r]<0 || self->sargs[f[7]+r]>=svec[f[6]].len/4) HMF_BAD();
      }
      if(!hmf_runs_fit(runs,f[5],ou->width)) HMF_BAD();
      for(int64_t r=0;r<f[3];r++){
        if(rows[r]<0 || rows[r]>=ou->rows) HMF_BAD();
        float *z=ou->ptr+(size_t)rows[r]*(size_t)ou->width*2;
        for(int64_t k=0;k<f[5];k++){
          const int64_t a=runs[2*k], b=runs[2*k+1];
          if(b<=a) continue;
          if(sv) hmf_scale_run(z+2*a,(size_t)(b-a),sv[self->sargs[f[7]+r]]);
          else memset(z+2*a,0,(size_t)(b-a)*8);
        }
      }
      break;
    }
    case HMF_OP_COPY: {
      if(f[1]<0 || f[1]>=nouts || f[3]<0 || f[3]>=nouts || !HMF_RANGE_OK(f[5],f[6],2)) HMF_BAD();
      const hmf_out_slot *src=&oslots[f[1]], *dst=&oslots[f[3]];
      const int64_t *runs=self->sargs+f[5];
      if(f[2]<0 || f[2]>=src->rows || f[4]<0 || f[4]>=dst->rows || src->width!=dst->width
         || !hmf_runs_fit(runs,f[6],src->width)) HMF_BAD();
      const float *sp=src->ptr+(size_t)f[2]*(size_t)src->width*2;
      float *dp=dst->ptr+(size_t)f[4]*(size_t)dst->width*2;
      for(int64_t k=0;k<f[6];k++){
        const int64_t a=runs[2*k], b=runs[2*k+1];
        if(b<=a) continue;
        if(f[7]){ ap_mf_stream_copy(dp+2*a,sp+2*a,(size_t)(b-a)*8); streamed=1; }
        else memcpy(dp+2*a,sp+2*a,(size_t)(b-a)*8);
      }
      break;
    }
    case HMF_OP_LANE: {
      if(f[1]<0 || f[1]>=nouts || f[4]<0 || f[4]>=self->nslots || (f[3]!=0 && f[3]!=1)
         || !HMF_RANGE_OK(f[5],f[6],2)) HMF_BAD();
      const hmf_out_slot *src=&oslots[f[1]]; const hmf_slot *dst=&slots[f[4]];
      const int64_t *runs=self->sargs+f[5];
      if(f[2]<0 || f[2]>=src->rows || dst->kind!=1 || dst->view.readonly
         || dst->samples!=src->width || !hmf_runs_fit(runs,f[6],src->width)) HMF_BAD();
      const float *sp=src->ptr+(size_t)f[2]*(size_t)src->width*2+f[3];
      float *dp=(float*)dst->ptr;
      for(int64_t k=0;k<f[6];k++)
        for(int64_t i=runs[2*k];i<runs[2*k+1];i++) dp[i]=sp[2*i];
      break;
    }
    case HMF_OP_COLLAR: {
      if(f[2]<0 || f[2]>=nouts || f[3]<0 || f[3]>=ntiles) HMF_BAD();
      const hmf_out_slot *sc=&oslots[f[2]];
      const int64_t kr=f[5], lo=f[6], hi=f[7], len=hi-lo;
      if(kr<0 || kr>sc->rows || lo<0 || hi>sc->width || len<0
         || (f[4]+kr*len)*8>tiles[f[3]].len || f[4]<0) HMF_BAD();
      float *carry=(float*)tiles[f[3]].ptr+2*f[4];
      for(int64_t q=0;q<kr;q++){
        float *row=sc->ptr+((size_t)q*(size_t)sc->width+(size_t)lo)*2;
        if(f[1]) memcpy(row,carry+2*q*len,(size_t)len*8);
        else memcpy(carry+2*q*len,row,(size_t)len*8);
      }
      break;
    }
    case HMF_OP_LEAF: {
      const int64_t n=f[2];
      if(!HMF_RANGE_OK(f[1],n,5)) HMF_BAD();
      double thr; memcpy(&thr,&f[4],8);
      for(int q=0;q<npos;q++) pos[q].n=0;
      if(!n) break;
      if(hmf_grow((void**)&jobs,&jcap,(size_t)n,sizeof(ap_hmf_sparse_job))){ PyErr_NoMemory(); goto done; }
      const int64_t *it=self->sargs+f[1];
      for(int64_t k=0;k<n;k++){
        const int64_t st=it[5*k], b0=it[5*k+1], b1=it[5*k+2];
        if(st<0 || st>=self->nsteps || self->steps[st].phase!=-1 || b0<0 || b1<=b0
           || b1>self->steps[st].nblocks || it[5*k+4]<0 || it[5*k+4]>=8) HMF_BAD();
        hmf_step *s=&self->steps[st];
        if(!hmf_step_mode_ok(s,&slots[s->slot])) HMF_BAD();
        if(s->hmf->busy){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter in use by another thread; use one filter per thread"); goto done; }
        if(hmf_step_set_mode(s)) goto done;
        hmf_job_bind(&jobs[k],s,&slots[s->slot],(int)b0,(int)b1,(int)it[5*k+3]);
      }
      for(int64_t k=0;k<n;k++) self->steps[it[5*k]].hmf->busy=1;
      int brc;
      const double t1=hmf_now();
      Py_BEGIN_ALLOW_THREADS
      brc=ap_hmf_run_series_batch_sparse(jobs,(int)n);
      Py_END_ALLOW_THREADS
      const double dt=hmf_now()-t1;
      for(int64_t k=0;k<n;k++) self->steps[it[5*k]].hmf->busy=0;
      if(brc<0){
        for(int64_t k=0;k<n;k++){ free(jobs[k].out_flat); free(jobs[k].out_idx); free(jobs[k].out_val); }
        PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done;
      }
      *leaf_seconds+=dt;
      int err=0;
      for(int64_t k=0;k<n && !err;k++){
        const ap_hmf_sparse_job *jb=&jobs[k];
        const int64_t st=it[5*k], b0=it[5*k+1], q=it[5*k+4];
        const hmf_step *s=&self->steps[st];
        const int64_t per_block=(int64_t)s->nt*(int64_t)s->nbins;
        hmf_parts *pt=&parts[st];
        pt->total+=jb->total; pt->seconds+=dt/(double)n;
        if(jb->total>0){
          if(hmf_parts_add(pt,b0,per_block,jb)){ err=1; break; }
          if(f[3]){
            if(q>=npos){
              hmf_posv *np2=realloc(pos,(size_t)(q+1)*sizeof(hmf_posv));
              if(!np2){ err=1; break; }
              pos=np2; for(int z=npos;z<=q;z++){ pos[z].pos=NULL; pos[z].n=pos[z].cap=0; } npos=(int)q+1;
            }
            for(size_t m=0;m<jb->out_count;m++){
              const float re=jb->out_val[2*m], im=jb->out_val[2*m+1];
              if(thr<=0.0 || hypotf(re,im)>=(float)thr){
                if(hmf_grow((void**)&pos[q].pos,&pos[q].cap,pos[q].n+1,8)){ err=1; break; }
                pos[q].pos[pos[q].n++]=(int64_t)s->starts[b0+jb->out_flat[m]/per_block]+jb->out_idx[m];
              }
            }
          }
        }
      }
      for(int64_t k=0;k<n;k++){ free(jobs[k].out_flat); free(jobs[k].out_idx); free(jobs[k].out_val); }
      if(err){ PyErr_NoMemory(); goto done; }
      break;
    }
    case HMF_OP_PENDING: {
      if(f[1]<0) HMF_BAD();
      if(f[1]>npending){
        int64_t *p2=realloc(pending,(size_t)f[1]*8); if(!p2){ PyErr_NoMemory(); goto done; }
        pending=p2; npending=f[1];
      }
      memset(pending,0,(size_t)f[1]*8);
      break;
    }
    case HMF_OP_RETAIN: {
      if(!HMF_RANGE_OK(f[1],15,1)) HMF_BAD();
      const int64_t *h=self->sargs+f[1];
      const int64_t kr=h[0], kr0=h[1], D=h[2], sc0=h[3], ou0=h[4], valid_lo=h[6], c_start=h[7],
                    c_end=h[8], R=h[11], S=h[12], pend=h[13];
      if(!HMF_RANGE_OK(h[5],kr,1) || !HMF_RANGE_OK(h[9],h[10],2) || sc0<0 || sc0+D>nouts
         || ou0<0 || ou0+D>nouts || (pend && kr0+kr>npending)) HMF_BAD();
      const int64_t *wr=self->sargs+h[9];
      for(int64_t q=0;q<kr;q++){
        size_t ns2=0;
        const int64_t kq=kr0+q;
        const hmf_posv *pv=q<npos?&pos[q]:NULL;
        const size_t np_=pv?pv->n:0;
        if(hmf_grow((void**)&spans,&scap,2*(np_+1),8)){ PyErr_NoMemory(); goto done; }
        if(pend && pending[kq]>c_start){
          spans[0]=c_start; spans[1]=c_end<pending[kq]?c_end:pending[kq]; ns2=1;
        }
        if(np_){
          if(pend){
            int64_t mx=pv->pos[0];
            for(size_t m=1;m<np_;m++) if(pv->pos[m]>mx) mx=pv->pos[m];
            const int64_t fwd=mx+R;
            if(fwd>c_end && fwd>pending[kq]) pending[kq]=S<fwd?S:fwd;
          }
          for(size_t m=0;m<np_;m++){
            const int64_t ca=valid_lo>pv->pos[m]-R?valid_lo:pv->pos[m]-R;
            const int64_t cb=c_end<pv->pos[m]+R?c_end:pv->pos[m]+R;
            if(cb>ca){ spans[2*ns2]=ca; spans[2*ns2+1]=cb; ns2++; }
          }
        }
        if(!ns2) continue;
        /* sort the spans as (start, end) pairs, merge, intersect with the written runs */
        for(size_t a=1;a<ns2;a++){
          const int64_t x0=spans[2*a], x1=spans[2*a+1]; size_t b=a;
          while(b>0 && (spans[2*(b-1)]>x0 || (spans[2*(b-1)]==x0 && spans[2*(b-1)+1]>x1))){
            spans[2*b]=spans[2*(b-1)]; spans[2*b+1]=spans[2*(b-1)+1]; b--;
          }
          spans[2*b]=x0; spans[2*b+1]=x1;
        }
        size_t nm=1;
        for(size_t a=1;a<ns2;a++){
          if(spans[2*a]<=spans[2*(nm-1)+1]){
            if(spans[2*a+1]>spans[2*(nm-1)+1]) spans[2*(nm-1)+1]=spans[2*a+1];
          } else { spans[2*nm]=spans[2*a]; spans[2*nm+1]=spans[2*a+1]; nm++; }
        }
        const int64_t row_out=self->sargs[h[5]+q];
        for(int64_t d=0;d<D;d++){
          const hmf_out_slot *src=&oslots[sc0+d], *dst=&oslots[ou0+d];
          if(q>=src->rows || row_out<0 || row_out>=dst->rows || src->width!=dst->width) HMF_BAD();
          const float *sp=src->ptr+(size_t)q*(size_t)src->width*2;
          float *dp=dst->ptr+(size_t)row_out*(size_t)dst->width*2;
          size_t i=0, j=0;
          while(i<nm && j<(size_t)h[10]){
            const int64_t a=spans[2*i]>wr[2*j]?spans[2*i]:wr[2*j];
            const int64_t b=spans[2*i+1]<wr[2*j+1]?spans[2*i+1]:wr[2*j+1];
            if(a<b){
              if(a<0 || b>src->width) HMF_BAD();
              if(h[14]){ ap_mf_stream_copy(dp+2*a,sp+2*a,(size_t)(b-a)*8); streamed=1; }
              else memcpy(dp+2*a,sp+2*a,(size_t)(b-a)*8);
            }
            if(spans[2*i+1]<wr[2*j+1]) i++; else j++;
          }
        }
      }
      for(int q=0;q<npos;q++) pos[q].n=0;
      break;
    }
    default: HMF_BAD();
    }
    if(f[0]!=HMF_OP_LEAF) *corr_seconds+=hmf_now()-t0;
  }
  if(streamed) ap_mf_stream_fence();
  rc=0;
done:
#undef HMF_BAD
  free(jobs); free(pending); free(spans);
  for(int q=0;q<npos;q++) free(pos[q].pos);
  free(pos);
  return rc;
}
/* The window-bin merges of one job's peaks, arena entries [job0, at): for each bin size of
   merge_bs in order, the partial bins of a window bin merged into one (hmf_merge_bins), the
   kept entries moved down in order. keep holds at least at - job0 entries. Returns the job's
   new end, or -1 with the exception set. Shared by HMFTable.run and assemble_peaks (the
   latter with numpy_magnitude: hmf_merge_bins). */
static Py_ssize_t hmf_job_merge(const int64_t *win_starts,Py_ssize_t nwin,const Py_ssize_t *merge_bs,
                                int nmerge,int64_t *o_t,double *o_s,float *o_v,int64_t *o_bs,
                                int64_t *o_bl,Py_ssize_t job0,Py_ssize_t at,Py_ssize_t *keep,
                                int numpy_magnitude){
  for(int k=0;k<nmerge && at>job0;k++){
    const Py_ssize_t kept=hmf_merge_bins(win_starts,nwin,(int64_t)merge_bs[k],o_t+job0,o_s+job0,
                                         o_v+2*job0,at-job0,keep,numpy_magnitude);
    if(kept==-2){ PyErr_SetString(PyExc_ValueError,"window_bin_keep: mismatched buffers, binsize < 1 or a peak before the first window"); return -1; }
    if(kept<0){ PyErr_NoMemory(); return -1; }
    for(Py_ssize_t q=0;q<kept;q++){
      const Py_ssize_t src=job0+keep[q], dst=job0+q;
      o_t[dst]=o_t[src]; o_s[dst]=o_s[src]; o_bs[dst]=o_bs[src]; o_bl[dst]=o_bl[src];
      o_v[2*dst]=o_v[2*src]; o_v[2*dst+1]=o_v[2*src+1];
    }
    at=job0+kept;
  }
  return at;
}
/* The arena's sample column, assembled as doubles (the merge compares them as the bank's
   Python assembly did), rewritten in place as int64, as FilterResults has it. */
static void hmf_samples_to_int(double *o_s,Py_ssize_t count){
  int64_t *o_si=(int64_t*)o_s;
  for(Py_ssize_t q=0;q<count;q++) o_si[q]=(int64_t)o_s[q];
}

/* ---------------- device readbacks, assembled as the table assembles its steps ----------------
   A GPU call's peaks arrive as the buffers its recording reads back (_gpuhier.Readback: the
   counts words, the survivor rows, the dense lags and values, or the compacted list), one part
   per batch of blocks. assemble_peaks reads every part of every call of every job of a batch,
   and assembles each job's peaks into one arena with the functions HMFTable.run uses
   (hmf_append_peaks, hmf_job_merge), in the order filter_series' Python assembly gave them:
   each call's peaks block-major in output rows (the layout's order), then template, then bin;
   for a call whose blocks have different bin counts, the blocks of each count in increasing
   count, each block's bins past its count dropped (one run_series call per count gave them
   so); a job's calls in order, then its window-bin merges. A part that was already read into
   host arrays (a result collected early, or a result of a call the device path does not read
   back: a _SparsePeaks, or dense (lags, values) arrays) is read from those. */

/* A call's peaks gathered from its parts: per peak the flat (row, template, bin) index over the
   call's computed rows, the lag in its block and the value (re, im). malloc'd. */
typedef struct { int64_t *flat, *idx; float *val; size_t n, cap; } hmf_gather;
static int hmf_gather_room(hmf_gather *g,size_t more){
  const size_t need=g->n+more;
  if(need<=g->cap) return 0;
  size_t c=g->cap?g->cap:256; while(c<need) c*=2;
  int64_t *f=realloc(g->flat,c*8); if(!f){ PyErr_NoMemory(); return -1; } g->flat=f;
  int64_t *i=realloc(g->idx,c*8); if(!i){ PyErr_NoMemory(); return -1; } g->idx=i;
  float *v=realloc(g->val,c*8); if(!v){ PyErr_NoMemory(); return -1; } g->val=v;
  g->cap=c; return 0;
}
/* Sort g's entries [from, n) by flat index (distinct within a part), in place. 0, or -1 with
   MemoryError set. */
static int hmf_gather_sort(hmf_gather *g,size_t from){
  const size_t m=g->n-from;
  int sorted=1;
  for(size_t q=from+1;q<g->n && sorted;q++) if(g->flat[q]<=g->flat[q-1]) sorted=0;
  if(sorted) return 0;
  hmf_flat *ord=PyMem_Malloc(m*sizeof(hmf_flat));
  int64_t *ti=PyMem_Malloc(m*8); float *tv=PyMem_Malloc(m*8);
  if(!ord||!ti||!tv){ PyMem_Free(ord); PyMem_Free(ti); PyMem_Free(tv); PyErr_NoMemory(); return -1; }
  for(size_t q=0;q<m;q++){ ord[q].key=g->flat[from+q]; ord[q].i=(Py_ssize_t)q; }
  qsort(ord,m,sizeof(hmf_flat),hmf_flat_cmp);
  for(size_t q=0;q<m;q++){
    const size_t src=from+(size_t)ord[q].i;
    ti[q]=g->idx[src]; tv[2*q]=g->val[2*src]; tv[2*q+1]=g->val[2*src+1];
  }
  for(size_t q=0;q<m;q++){
    g->flat[from+q]=ord[q].key; g->idx[from+q]=ti[q];
    g->val[2*(from+q)]=tv[2*q]; g->val[2*(from+q)+1]=tv[2*q+1];
  }
  PyMem_Free(ord); PyMem_Free(ti); PyMem_Free(tv);
  return 0;
}
/* A readable C-contiguous view of o of at least nbytes (any length when nbytes < 0). 0, or -1
   with the exception set. */
static int hmf_view_of(PyObject *o,Py_buffer *b,Py_ssize_t nbytes,const char *what){
  if(PyObject_GetBuffer(o,b,PyBUF_C_CONTIGUOUS)<0) return -1;
  if(nbytes>=0 && b->len<nbytes){
    PyBuffer_Release(b);
    PyErr_Format(PyExc_ValueError,"assemble_peaks: the %s readback is shorter than its count",what);
    return -1;
  }
  return 0;
}
/* The counters of one device readback (the counts words its compaction kernels wrote):
   refined (the last tier's survivors), tier-1 passes (a cascade's tier 0), direct and
   transform refines, and the count of compacted peaks. */
typedef struct { int64_t pairs, refined, tier1, direct, fft, listed, t0_checked; int device; } hmf_rb_counts;
static int hmf_i64_cmp(const void *a,const void *b){
  const int64_t x=*(const int64_t*)a,y=*(const int64_t*)b; return (x>y)-(x<y);
}
/* Read one part into g, its flat indices offset by base (the flat index of its first row in
   the call), in flat order. The part is a device readback, a tuple
   (way, rows, templates, bins, counts, w_refined, w_listed, w_fft, w_tier1, t0_checked,
   survivors, lags, values, list): way 0 dense (every bin of the lags and values; -1 in an
   empty bin), 1 the survivor rows' bins, 2 the compacted (position, lag, re, im) records;
   counts the counts words (uint32) and w_* the word of each counter (-1: none); or a
   _SparsePeaks (flat, idx, val); or dense (lags, values) of shape (rows, templates, bins).
   nt and nbins are the call's: a part of another shape is an error. With rc given, a device
   readback's counters are written there (zeros for the other forms). 0, or -1 with the
   exception set. */
static int hmf_read_part(PyObject *part,int64_t base,int64_t nt,int64_t nbins,hmf_gather *g,
                         hmf_rb_counts *rc){
  hmf_rb_counts zero={0,0,0,0,0,0,0,0};
  if(rc) *rc=zero;
  const int64_t per_block=nt*nbins;
  if(PyTuple_Check(part) && PyTuple_GET_SIZE(part)==14 && PyLong_Check(PyTuple_GET_ITEM(part,0))){
    long long way,nd,pnt,pnb,w_ref,w_list,w_fft,w_t1,t0c;
    PyObject *counts,*surv,*lags,*vals,*list;
    if(!PyArg_ParseTuple(part,"LLLLOLLLLLOOOO",&way,&nd,&pnt,&pnb,&counts,&w_ref,&w_list,&w_fft,
                         &w_t1,&t0c,&surv,&lags,&vals,&list)) return -1;
    if(pnt!=nt || pnb!=nbins || nd<0 || way<0 || way>2){
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a readback's shape is not its call's");
      return -1;
    }
    Py_buffer bc;
    if(hmf_view_of(counts,&bc,-1,"counts")) return -1;
    const uint32_t *w=(const uint32_t*)bc.buf; const Py_ssize_t nw=bc.len/4;
    if(w_ref<0 || w_ref>=nw || w_list>=nw || w_fft>=nw || w_t1>=nw){
      PyBuffer_Release(&bc);
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a counter word is outside the counts");
      return -1;
    }
    hmf_rb_counts c;
    c.device=1; c.pairs=nd*nt; c.refined=w[w_ref]; c.tier1=w_t1>=0?w[w_t1]:0; c.listed=w_list>=0?w[w_list]:0;
    c.t0_checked=t0c;
    if(w_fft>=0){ const int64_t fb=w[w_fft]; c.fft=fb; c.direct=c.refined>fb?c.refined-fb:0; }
    else { c.fft=c.refined; c.direct=0; }
    PyBuffer_Release(&bc);
    if(rc) *rc=c;
    const int64_t pairs=nd*nt, out=pairs*nbins;
    if(!g || c.refined==0) return 0;
    const size_t from=g->n;
    if(way==2){
      Py_buffer bl;
      if(hmf_view_of(list,&bl,(Py_ssize_t)c.listed*16,"list")) return -1;
      const uint32_t *r=(const uint32_t*)bl.buf;
      if(hmf_gather_room(g,(size_t)c.listed)){ PyBuffer_Release(&bl); return -1; }
      for(int64_t q=0;q<c.listed;q++){
        const int64_t pos=r[4*q];
        if(pos>=out){ PyBuffer_Release(&bl); PyErr_SetString(PyExc_ValueError,"assemble_peaks: a listed peak is outside its readback"); return -1; }
        g->flat[g->n]=pos+base; g->idx[g->n]=(int32_t)r[4*q+1];
        memcpy(&g->val[2*g->n],&r[4*q+2],8); g->n++;
      }
      PyBuffer_Release(&bl);
    } else {
      Py_buffer bi,bv,bs; int held_s=0;
      if(hmf_view_of(lags,&bi,out*4,"lags")) return -1;
      if(hmf_view_of(vals,&bv,out*8,"values")){ PyBuffer_Release(&bi); return -1; }
      const int32_t *ix=(const int32_t*)bi.buf; const float *vv=(const float*)bv.buf;
      int fail=0;
      if(way==0){
        for(int64_t f=0;f<out && !fail;f++)
          if(ix[f]>=0){
            if(hmf_gather_room(g,1)){ fail=1; break; }
            g->flat[g->n]=f+base; g->idx[g->n]=ix[f];
            g->val[2*g->n]=vv[2*f]; g->val[2*g->n+1]=vv[2*f+1]; g->n++;
          }
      } else if(hmf_view_of(surv,&bs,(Py_ssize_t)c.refined*4,"survivors")) fail=1;
      else {
        held_s=1;
        const uint32_t *rows=(const uint32_t*)bs.buf;
        for(int64_t q=0;q<c.refined && !fail;q++){
          const int64_t r=rows[q];
          if(r>=pairs){ PyErr_SetString(PyExc_ValueError,"assemble_peaks: a survivor row is outside its readback"); fail=1; break; }
          for(int64_t b=0;b<nbins;b++){
            const int64_t f=r*nbins+b;
            if(ix[f]<0) continue;
            if(hmf_gather_room(g,1)){ fail=1; break; }
            g->flat[g->n]=f+base; g->idx[g->n]=ix[f];
            g->val[2*g->n]=vv[2*f]; g->val[2*g->n+1]=vv[2*f+1]; g->n++;
          }
        }
      }
      if(held_s) PyBuffer_Release(&bs);
      PyBuffer_Release(&bi); PyBuffer_Release(&bv);
      if(fail) return -1;
    }
    return hmf_gather_sort(g,from);
  }
  if(!g) return 0;
  if(PyTuple_Check(part) && PyTuple_GET_SIZE(part)==2){
    /* dense (lags, values): lags int32 or int64, -1 in an empty bin */
    Py_buffer bi,bv;
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(part,0),&bi,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return -1;
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(part,1),&bv,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&bi); return -1; }
    int ok=bi.ndim==3 && bv.ndim==3 && (bi.itemsize==4 || bi.itemsize==8) && bv.itemsize==8
           && bi.shape[1]==nt && bi.shape[2]==nbins && bv.shape[0]==bi.shape[0]
           && bv.shape[1]==nt && bv.shape[2]==nbins;
    if(!ok){
      PyBuffer_Release(&bi); PyBuffer_Release(&bv);
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a dense part is not (rows, templates, bins) lags and complex64 values of its call's shape");
      return -1;
    }
    const int64_t out=(int64_t)bi.shape[0]*per_block;
    const float *vv=(const float*)bv.buf; int fail=0;
    for(int64_t f=0;f<out;f++){
      const int64_t lag=bi.itemsize==4?(int64_t)((const int32_t*)bi.buf)[f]:((const int64_t*)bi.buf)[f];
      if(lag<0) continue;
      if(hmf_gather_room(g,1)){ fail=1; break; }
      g->flat[g->n]=f+base; g->idx[g->n]=lag;
      g->val[2*g->n]=vv[2*f]; g->val[2*g->n+1]=vv[2*f+1]; g->n++;
    }
    PyBuffer_Release(&bi); PyBuffer_Release(&bv);
    return fail?-1:0;
  }
  /* a _SparsePeaks: flat indices over its shape, lags, values, in flat order */
  PyObject *shape=PyObject_GetAttrString(part,"shape");
  if(!shape) return -1;
  long long snd=0,snt=0,snb=0;
  const int shaped=PyArg_ParseTuple(shape,"LLL",&snd,&snt,&snb);
  Py_DECREF(shape);
  if(!shaped) return -1;
  if(snt!=nt || snb!=nbins){
    PyErr_SetString(PyExc_ValueError,"assemble_peaks: a sparse part's shape is not its call's");
    return -1;
  }
  PyObject *fo=PyObject_GetAttrString(part,"flat"),*io=PyObject_GetAttrString(part,"idx"),
           *vo=PyObject_GetAttrString(part,"val");
  int rcode=-1;
  Py_buffer bf,bi,bv; int held=0;
  if(!fo||!io||!vo) goto sparse_done;
  if(PyObject_GetBuffer(fo,&bf,PyBUF_C_CONTIGUOUS)<0) goto sparse_done;
  held=1;
  if(PyObject_GetBuffer(io,&bi,PyBUF_C_CONTIGUOUS)<0) goto sparse_done;
  held=2;
  if(PyObject_GetBuffer(vo,&bv,PyBUF_C_CONTIGUOUS)<0) goto sparse_done;
  held=3;
  {
    const Py_ssize_t m=bf.len/8;
    if(bi.len!=m*8 || bv.len!=m*8){
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a sparse part's columns differ in length");
      goto sparse_done;
    }
    if(hmf_gather_room(g,(size_t)m)) goto sparse_done;
    const int64_t *ff=bf.buf,*ii=bi.buf; const float *vv=bv.buf;
    for(Py_ssize_t q=0;q<m;q++){
      if(ff[q]<0 || ff[q]>=snd*per_block){
        PyErr_SetString(PyExc_ValueError,"assemble_peaks: a sparse peak is outside its part");
        goto sparse_done;
      }
      g->flat[g->n]=ff[q]+base; g->idx[g->n]=ii[q];
      g->val[2*g->n]=vv[2*q]; g->val[2*g->n+1]=vv[2*q+1]; g->n++;
    }
  }
  rcode=0;
sparse_done:
  if(held>=3) PyBuffer_Release(&bv);
  if(held>=2) PyBuffer_Release(&bi);
  if(held>=1) PyBuffer_Release(&bf);
  Py_XDECREF(fo); Py_XDECREF(io); Py_XDECREF(vo);
  return rcode;
}
/* Append one call's gathered peaks (entries [from, to) of g, flat over its computed rows) to
   the arena at `at`, in the order described above: rows mapped to output rows by order (NULL:
   the computed order), (row, template, bin) order; with row_bins, each bin count's rows in
   increasing count, bins past a row's count dropped. Returns the new end, or -1 with the
   exception set. */
static Py_ssize_t hmf_append_call(int64_t *o_t,double *o_s,float *o_v,int64_t *o_bs,int64_t *o_bl,
                                  Py_ssize_t at,const hmf_gather *g,size_t from,size_t to,
                                  const int64_t *tmap,const int64_t *ostarts,const int64_t *order,
                                  const int64_t *row_bins,int64_t nrows,int64_t nt,int64_t nbins,
                                  size_t block_len){
  const int64_t per_block=nt*nbins;
  const Py_ssize_t m=(Py_ssize_t)(to-from);
  const int64_t *flat=g->flat+from,*idx=g->idx+from; const float *val=g->val+2*from;
  int sorted=1;
  for(Py_ssize_t q=0;q<m;q++){
    if(flat[q]<0 || flat[q]>=nrows*per_block){
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a peak's block is outside its call"); return -1;
    }
    if(q && flat[q]<=flat[q-1]) sorted=0;
  }
  if(order) for(int64_t r=0;r<nrows;r++) if(order[r]<0 || order[r]>=nrows){
    PyErr_SetString(PyExc_ValueError,"assemble_peaks: a call's order is not a row permutation"); return -1;
  }
  if(!row_bins){
    int64_t *ident=NULL;
    if(!order && !sorted){
      ident=PyMem_Malloc((size_t)(nrows?nrows:1)*8);
      if(!ident){ PyErr_NoMemory(); return -1; }
      for(int64_t r=0;r<nrows;r++) ident[r]=r;
    }
    at=hmf_append_peaks(o_t,o_s,o_v,o_bs,o_bl,at,tmap,ostarts,order?order:ident,nt,nbins,
                        block_len,m,flat,idx,val);
    PyMem_Free(ident);
    return at;
  }
  /* the output-ordered peaks, then each bin count's rows (rank and start) and peaks */
  Py_ssize_t ret=-1;
  hmf_flat *key=PyMem_Malloc((size_t)(m?m:1)*sizeof(hmf_flat));
  int64_t *us=PyMem_Malloc((size_t)(nrows?nrows:1)*8), *rank=PyMem_Malloc((size_t)(nrows?nrows:1)*8);
  int64_t *gst=PyMem_Malloc((size_t)(nrows?nrows:1)*8), *gflat=PyMem_Malloc((size_t)(m?m:1)*8);
  int64_t *gidx=PyMem_Malloc((size_t)(m?m:1)*8); float *gval=PyMem_Malloc((size_t)(m?m:1)*8);
  if(!key||!us||!rank||!gst||!gflat||!gidx||!gval){ PyErr_NoMemory(); goto bins_done; }
  for(Py_ssize_t q=0;q<m;q++){
    const int64_t f=flat[q];
    key[q].key=order?order[f/per_block]*per_block+f%per_block:f; key[q].i=q;
  }
  if(order || !sorted) qsort(key,(size_t)m,sizeof(hmf_flat),hmf_flat_cmp);
  int64_t nu=0;
  for(int64_t r=0;r<nrows;r++) us[nu++]=row_bins[r];
  qsort(us,(size_t)nu,8,hmf_i64_cmp);
  {
    int64_t k=0;
    for(int64_t q=0;q<nu;q++) if(!q || us[q]!=us[q-1]) us[k++]=us[q];
    nu=k;
  }
  for(int64_t ui=0;ui<nu;ui++){
    const int64_t u=us[ui];
    int64_t nr=0;
    for(int64_t r=0;r<nrows;r++) if(row_bins[r]==u){ rank[r]=nr; gst[nr]=ostarts[r]; nr++; }
    Py_ssize_t gm=0;
    for(Py_ssize_t q=0;q<m;q++){
      const int64_t f=key[q].key, r=f/per_block, rest=f%per_block, t=rest/nbins, b=rest%nbins;
      if(row_bins[r]!=u || b>=u) continue;
      gflat[gm]=(rank[r]*nt+t)*u+b; gidx[gm]=idx[key[q].i];
      gval[2*gm]=val[2*key[q].i]; gval[2*gm+1]=val[2*key[q].i+1]; gm++;
    }
    at=hmf_append_peaks(o_t,o_s,o_v,o_bs,o_bl,at,tmap,gst,NULL,nt,u,block_len,gm,gflat,gidx,gval);
    if(at<0) goto bins_done;
  }
  ret=at;
bins_done:
  PyMem_Free(key); PyMem_Free(us); PyMem_Free(rank); PyMem_Free(gst); PyMem_Free(gflat);
  PyMem_Free(gidx); PyMem_Free(gval);
  return ret;
}
/* A call's geometry, (templates, block starts, order, row bin counts, nt, nbins, block length,
   counters): templates int64 [nt] the bank index of each template of the result; block starts
   int64 [rows] in output order; order int64 [rows] the output row of each computed row, or
   None; row bin counts int64 [rows], or None; counters int64 [6] (pairs, refined, tier-0
   passes, direct refines, transform refines, tier-0 pairs checked) the device readbacks'
   counts are added to, or None. */
typedef struct {
  Py_buffer tmap, ostarts, order, row_bins, counters; int held;
  long long nt, nbins, block_len, nrows;
} hmf_call_geom;
static void hmf_geom_release(hmf_call_geom *c){
  if(c->held&1) PyBuffer_Release(&c->tmap);
  if(c->held&2) PyBuffer_Release(&c->ostarts);
  if(c->held&4) PyBuffer_Release(&c->order);
  if(c->held&8) PyBuffer_Release(&c->row_bins);
  if(c->held&16) PyBuffer_Release(&c->counters);
  c->held=0;
}
static int hmf_geom_bind(PyObject *o,hmf_call_geom *c){
  memset(c,0,sizeof(*c));
  PyObject *tm,*st,*od,*rb,*ct;
  if(!PyArg_ParseTuple(o,"OOOOLLLO",&tm,&st,&od,&rb,&c->nt,&c->nbins,&c->block_len,&ct)) return -1;
  if(c->nt<1 || c->nbins<1 || c->block_len<1){
    PyErr_SetString(PyExc_ValueError,"assemble_peaks: a call's templates, bins and block length must be positive"); return -1;
  }
  if(PyObject_GetBuffer(tm,&c->tmap,PyBUF_C_CONTIGUOUS)<0) return -1;
  c->held|=1;
  if(PyObject_GetBuffer(st,&c->ostarts,PyBUF_C_CONTIGUOUS)<0) goto fail;
  c->held|=2;
  c->nrows=c->ostarts.len/8;
  if(c->tmap.len!=c->nt*8 || c->ostarts.len!=c->nrows*8){
    PyErr_SetString(PyExc_ValueError,"assemble_peaks: a call's templates or block starts are not 8-byte integers of its shape"); goto fail;
  }
  if(od!=Py_None){
    if(PyObject_GetBuffer(od,&c->order,PyBUF_C_CONTIGUOUS)<0) goto fail;
    c->held|=4;
    if(c->order.len!=c->nrows*8){ PyErr_SetString(PyExc_ValueError,"assemble_peaks: a call's order is not one int64 per block"); goto fail; }
  }
  if(rb!=Py_None){
    if(PyObject_GetBuffer(rb,&c->row_bins,PyBUF_C_CONTIGUOUS)<0) goto fail;
    c->held|=8;
    if(c->row_bins.len!=c->nrows*8){ PyErr_SetString(PyExc_ValueError,"assemble_peaks: a call's bin counts are not one int64 per block"); goto fail; }
  }
  if(ct!=Py_None){
    if(PyObject_GetBuffer(ct,&c->counters,PyBUF_C_CONTIGUOUS|PyBUF_WRITABLE)<0) goto fail;
    c->held|=16;
    if(c->counters.len!=6*8){ PyErr_SetString(PyExc_ValueError,"assemble_peaks: counters must be int64 [6]"); goto fail; }
  }
  return 0;
fail:
  hmf_geom_release(c);
  return -1;
}
/* assemble_peaks(jobs) -> (offsets, templates, samples, snr, block_starts, block_lengths). */
static PyObject *M_assemble_peaks(PyObject *self,PyObject *jobs_arg){
  (void)self;
  PyObject *jobs=PySequence_Fast(jobs_arg,"jobs must be a sequence");
  if(!jobs) return NULL;
  const Py_ssize_t nj=PySequence_Fast_GET_SIZE(jobs);
  PyObject *ret=NULL;
  hmf_gather g; memset(&g,0,sizeof(g));
  size_t *bounds=NULL; Py_ssize_t ncalls=0, cap_calls=0;
  int64_t *o_t=NULL; Py_ssize_t *keep=NULL;
  /* every part of every call read, the calls' entry ranges kept */
  for(Py_ssize_t j=0;j<nj;j++){
    PyObject *job=PySequence_Fast_GET_ITEM(jobs,j);
    if(!PyTuple_Check(job) || PyTuple_GET_SIZE(job)!=3){
      PyErr_SetString(PyExc_ValueError,"assemble_peaks: a job is (calls, window starts, merge bin sizes)"); goto done;
    }
    PyObject *calls=PySequence_Fast(PyTuple_GET_ITEM(job,0),"a job's calls must be a sequence");
    if(!calls) goto done;
    for(Py_ssize_t c=0;c<PySequence_Fast_GET_SIZE(calls);c++){
      PyObject *call=PySequence_Fast_GET_ITEM(calls,c);
      PyObject *geom,*parts;
      if(!PyArg_ParseTuple(call,"OO",&geom,&parts)){ Py_DECREF(calls); goto done; }
      hmf_call_geom cg;
      if(hmf_geom_bind(geom,&cg)){ Py_DECREF(calls); goto done; }
      PyObject *ps=PySequence_Fast(parts,"a call's parts must be a sequence");
      int fail=!ps;
      const size_t from=g.n;
      for(Py_ssize_t p=0;!fail && p<PySequence_Fast_GET_SIZE(ps);p++){
        long long b0; PyObject *part; hmf_rb_counts rc;
        if(!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(ps,p),"LO",&b0,&part)
           || b0<0 || b0>cg.nrows){ if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"assemble_peaks: a part's first block is outside its call"); fail=1; break; }
        if(hmf_read_part(part,b0*cg.nt*cg.nbins,cg.nt,cg.nbins,&g,&rc)){ fail=1; break; }
        if((cg.held&16) && rc.device){
          int64_t *w=cg.counters.buf;
          w[0]+=rc.pairs; w[1]+=rc.refined; w[2]+=rc.tier1; w[3]+=rc.direct; w[4]+=rc.fft;
          w[5]+=rc.t0_checked;
        }
      }
      Py_XDECREF(ps);
      hmf_geom_release(&cg);
      if(fail){ Py_DECREF(calls); goto done; }
      if(ncalls+1>cap_calls){
        cap_calls=cap_calls?2*cap_calls:64;
        size_t *nb=realloc(bounds,(size_t)cap_calls*2*sizeof(size_t));
        if(!nb){ PyErr_NoMemory(); Py_DECREF(calls); goto done; }
        bounds=nb;
      }
      bounds[2*ncalls]=from; bounds[2*ncalls+1]=g.n; ncalls++;
    }
    Py_DECREF(calls);
  }
  /* the arena: each job's calls appended in order, then its merges */
  const size_t cap=g.n?g.n:1;
  o_t=PyMem_Malloc(cap*5*8+((size_t)nj+1)*8);
  keep=PyMem_Malloc(cap*sizeof(Py_ssize_t));
  if(!o_t||!keep){ PyErr_NoMemory(); goto done; }
  double *o_s=(double*)(o_t+cap); float *o_v=(float*)(o_t+2*cap);
  int64_t *o_bs=o_t+3*cap, *o_bl=o_t+4*cap, *offs=o_t+5*cap;
  Py_ssize_t at=0, ci=0;
  for(Py_ssize_t j=0;j<nj;j++){
    PyObject *job=PySequence_Fast_GET_ITEM(jobs,j);
    offs[j]=at;
    const Py_ssize_t job0=at;
    PyObject *calls=PySequence_Fast(PyTuple_GET_ITEM(job,0),"a job's calls must be a sequence");
    if(!calls) goto done;
    for(Py_ssize_t c=0;c<PySequence_Fast_GET_SIZE(calls);c++,ci++){
      hmf_call_geom cg;
      if(hmf_geom_bind(PyTuple_GET_ITEM(PySequence_Fast_GET_ITEM(calls,c),0),&cg)){ Py_DECREF(calls); goto done; }
      if(bounds[2*ci+1]>bounds[2*ci])
        at=hmf_append_call(o_t,o_s,o_v,o_bs,o_bl,at,&g,bounds[2*ci],bounds[2*ci+1],cg.tmap.buf,
                           cg.ostarts.buf,(cg.held&4)?cg.order.buf:NULL,
                           (cg.held&8)?cg.row_bins.buf:NULL,cg.nrows,cg.nt,cg.nbins,
                           (size_t)cg.block_len);
      hmf_geom_release(&cg);
      if(at<0){ Py_DECREF(calls); goto done; }
    }
    Py_DECREF(calls);
    PyObject *ws=PyTuple_GET_ITEM(job,1), *mb=PyTuple_GET_ITEM(job,2);
    if(ws!=Py_None && at>job0){
      PyObject *mbs=PySequence_Fast(mb,"merge bin sizes must be a sequence");
      if(!mbs) goto done;
      const Py_ssize_t nm=PySequence_Fast_GET_SIZE(mbs);
      Py_ssize_t sizes[16];
      if(nm>16){ Py_DECREF(mbs); PyErr_SetString(PyExc_ValueError,"assemble_peaks: at most 16 merge bin sizes"); goto done; }
      for(Py_ssize_t k=0;k<nm;k++) sizes[k]=PyLong_AsSsize_t(PySequence_Fast_GET_ITEM(mbs,k));
      Py_DECREF(mbs);
      if(PyErr_Occurred()) goto done;
      Py_buffer bw;
      if(PyObject_GetBuffer(ws,&bw,PyBUF_C_CONTIGUOUS)<0) goto done;
      at=hmf_job_merge(bw.buf,bw.len/8,sizes,(int)nm,o_t,o_s,o_v,o_bs,o_bl,job0,at,keep,1);
      PyBuffer_Release(&bw);
      if(at<0) goto done;
    }
  }
  offs[nj]=at;
  hmf_samples_to_int(o_s,at);
  ret=Py_BuildValue("(NNNNNN)",hmf_bytes(offs,(nj+1)*8),hmf_bytes(o_t,at*8),hmf_bytes(o_s,at*8),
                    hmf_bytes(o_v,at*8),hmf_bytes(o_bs,at*8),hmf_bytes(o_bl,at*8));
done:
  free(g.flat); free(g.idx); free(g.val); free(bounds);
  PyMem_Free(o_t); PyMem_Free(keep);
  Py_DECREF(jobs);
  return ret;
}
/* device_peaks(readback, peaks=True) -> (flat, lags, values, refined, tier1, direct, fft,
   t0_checked): one device readback read into host arrays (bytearrays: int64 flat indices over
   its (rows, templates, bins), int64 lags, complex64 values, in flat order; None without
   peaks) and its counters, by the reader assemble_peaks uses. */
static PyObject *M_device_peaks(PyObject *self,PyObject *args){
  (void)self;
  PyObject *part; int peaks=1;
  if(!PyArg_ParseTuple(args,"O|p",&part,&peaks)) return NULL;
  if(!PyTuple_Check(part) || PyTuple_GET_SIZE(part)!=14){
    PyErr_SetString(PyExc_ValueError,"device_peaks: a device readback tuple is required"); return NULL;
  }
  const long long nt=PyLong_AsLongLong(PyTuple_GET_ITEM(part,2)), nb=PyLong_AsLongLong(PyTuple_GET_ITEM(part,3));
  if(PyErr_Occurred()) return NULL;
  hmf_gather g; memset(&g,0,sizeof(g)); hmf_rb_counts rc;
  if(hmf_read_part(part,0,nt,nb,peaks?&g:NULL,&rc)){ free(g.flat); free(g.idx); free(g.val); return NULL; }
  PyObject *ret;
  if(peaks){
    PyObject *f=PyByteArray_FromStringAndSize(g.n?(const char*)g.flat:"",(Py_ssize_t)g.n*8);
    PyObject *i=PyByteArray_FromStringAndSize(g.n?(const char*)g.idx:"",(Py_ssize_t)g.n*8);
    PyObject *v=PyByteArray_FromStringAndSize(g.n?(const char*)g.val:"",(Py_ssize_t)g.n*8);
    if(f&&i&&v)
      ret=Py_BuildValue("(NNNLLLLL)",f,i,v,(long long)rc.refined,(long long)rc.tier1,
                        (long long)rc.direct,(long long)rc.fft,(long long)rc.t0_checked);
    else { Py_XDECREF(f); Py_XDECREF(i); Py_XDECREF(v); ret=NULL; }
  } else {
    ret=Py_BuildValue("(OOOLLLLL)",Py_None,Py_None,Py_None,(long long)rc.refined,(long long)rc.tier1,
                      (long long)rc.direct,(long long)rc.fft,(long long)rc.t0_checked);
  }
  free(g.flat); free(g.idx); free(g.val);
  return ret;
}
static PyObject *HMFTable_run(HMFTableObject *self,PyObject *args){
  PyObject *series_arg,*calls_arg=NULL,*outs_arg=NULL,*scales_arg=NULL,*tiles_arg=NULL;
  if(!PyArg_ParseTuple(args,"O|OOOO",&series_arg,&calls_arg,&outs_arg,&scales_arg,&tiles_arg))
    return NULL;
  if((self->ncorrs || self->ops) && (!outs_arg || outs_arg==Py_None)){
    PyErr_SetString(PyExc_ValueError,"HMFTable.run: a table with correlation steps needs its outputs");
    return NULL;
  }
  /* without a schedule, the correlation steps first, in order: the leaf steps may read what
     they write */
  double corr_seconds=0.0;
  if(self->ncorrs && !self->ops
     && hmf_run_corrs(self,0,self->ncorrs,series_arg,outs_arg,scales_arg,&corr_seconds))
    return NULL;
  PyObject *seq=PySequence_Fast(series_arg,"series must be a sequence");
  if(!seq) return NULL;
  PyObject *oseq=NULL,*sseq=NULL,*tseq=NULL;
  hmf_out_slot *oslots=NULL; Py_buffer *svec=NULL; hmf_tile *tiles=NULL; hmf_parts *parts=NULL;
  Py_ssize_t noslots=0,nsvec=0,ntiles=0;
  int *ui=NULL;
  hmf_single_out sing; memset(&sing,0,sizeof(sing));
  PyObject *ret=NULL;
  const int ns=self->nsteps;
  hmf_slot *slots=NULL; ap_hmf_sparse_job *jobs=NULL; hmf_span *spans=NULL;
  hmf_cluster *clusters=NULL; int *members=NULL, *exec_of=NULL, *totals=NULL;
  double *seconds=NULL; double kernel=0.0;
  int64_t *o_t=NULL,*o_bs=NULL,*o_bl=NULL,*offs=NULL; double *o_s=NULL; float *o_v=NULL;
  Py_ssize_t *keep=NULL;
  hmf_flat_out *fout=NULL; const int nf=self->nflats;
  if(PySequence_Fast_GET_SIZE(seq)!=self->nslots){
    PyErr_SetString(PyExc_ValueError,"HMFTable.run: one series per slot"); goto done;
  }
  /* the calls bound to the single-template steps */
  if(calls_arg && hmf_run_singles(self,calls_arg,&sing)) goto done;
  const Py_ssize_t nsc=sing.ncalls, nout=ns+nsc+nf;
  kernel+=sing.seconds;
  fout=PyMem_Calloc(nf?(size_t)nf:1,sizeof(hmf_flat_out));
  if(!fout){ PyErr_NoMemory(); goto done; }
  totals=PyMem_Calloc(nout?(size_t)nout:1,sizeof(int));
  seconds=PyMem_Calloc(nout?(size_t)nout:1,sizeof(double));
  if(!totals||!seconds){ PyErr_NoMemory(); goto done; }
  if(self->nslots || ns){
    slots=PyMem_Calloc(self->nslots?(size_t)self->nslots:1,sizeof(hmf_slot));
    jobs=PyMem_Calloc(ns?(size_t)ns:1,sizeof(ap_hmf_sparse_job));
    spans=PyMem_Calloc(ns?(size_t)ns:1,sizeof(hmf_span));
    clusters=PyMem_Calloc(ns?(size_t)ns:1,sizeof(hmf_cluster));
    members=PyMem_Calloc(ns?(size_t)ns:1,sizeof(int));
    exec_of=PyMem_Calloc(ns?(size_t)ns:1,sizeof(int));
    if(!slots||!jobs||!spans||!clusters||!members||!exec_of){ PyErr_NoMemory(); goto done; }
  }
  for(int k=0;k<self->nslots;k++)
    if(hmf_slot_bind(PySequence_Fast_GET_ITEM(seq,k),&slots[k])) goto done;
  for(int i=0;i<ns;i++){
    hmf_step *s=&self->steps[i];
    if(!hmf_step_mode_ok(s,&slots[s->slot])){
      PyErr_SetString(PyExc_ValueError,"HMFTable.run: a series is not of the kind its steps were compiled for");
      goto done;
    }
    if(s->hmf->busy){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter in use by another thread; use one filter per thread"); goto done; }
  }
  for(int i=0;i<nf;i++){
    const hmf_flat_step *f=&self->flats[i];
    const int kind=slots[f->slot].kind;
    if(f->real ? kind!=(f->stride==2?2:1) : kind!=0){
      PyErr_SetString(PyExc_ValueError,"HMFTable.run: a series is not of the kind its steps were compiled for");
      goto done;
    }
    if(f->mf->busy){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter in use by another thread; use one filter per thread"); goto done; }
  }
  /* the schedule: its outputs, scale vectors and tiles bound once, its ops in order */
  parts=PyMem_Calloc(ns?(size_t)ns:1,sizeof(hmf_parts));
  ui=PyMem_Calloc(ns?(size_t)ns:1,sizeof(int));
  if(!parts||!ui){ PyErr_NoMemory(); goto done; }
  for(int i=0;i<ns;i++) parts[i].monotone=1;
  if(self->ops){
    oseq=PySequence_Fast(outs_arg,"outputs must be a sequence");
    if(!oseq) goto done;
    if(PySequence_Fast_GET_SIZE(oseq)!=self->nouts){
      PyErr_SetString(PyExc_ValueError,"HMFTable: one array per output slot"); goto done;
    }
    oslots=PyMem_Calloc(self->nouts?(size_t)self->nouts:1,sizeof(hmf_out_slot));
    if(!oslots){ PyErr_NoMemory(); goto done; }
    for(Py_ssize_t k=0;k<self->nouts;k++){
      if(hmf_out_bind(PySequence_Fast_GET_ITEM(oseq,k),&oslots[k])){ noslots=k+1; goto done; }
      noslots=k+1;
    }
    if(scales_arg && scales_arg!=Py_None){
      sseq=PySequence_Fast(scales_arg,"scales must be a sequence");
      if(!sseq) goto done;
      const Py_ssize_t n=PySequence_Fast_GET_SIZE(sseq);
      svec=PyMem_Calloc(n?(size_t)n:1,sizeof(Py_buffer));
      if(!svec){ PyErr_NoMemory(); goto done; }
      for(Py_ssize_t k=0;k<n;k++){
        if(PyObject_GetBuffer(PySequence_Fast_GET_ITEM(sseq,k),&svec[k],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) goto done;
        nsvec=k+1;
        const char *fm=svec[k].format?svec[k].format:"B";
        if(*fm=='<' || *fm=='=' || *fm=='@') fm++;
        if(strcmp(fm,"f") || svec[k].itemsize!=4){
          PyErr_SetString(PyExc_ValueError,"HMFTable: scales must be float32"); goto done;
        }
      }
    }
    if(tiles_arg && tiles_arg!=Py_None){
      tseq=PySequence_Fast(tiles_arg,"tiles must be a sequence");
      if(!tseq) goto done;
      const Py_ssize_t n=PySequence_Fast_GET_SIZE(tseq);
      tiles=PyMem_Calloc(n?(size_t)n:1,sizeof(hmf_tile));
      if(!tiles){ PyErr_NoMemory(); goto done; }
      for(Py_ssize_t k=0;k<n;k++){
        if(PyObject_GetBuffer(PySequence_Fast_GET_ITEM(tseq,k),&tiles[k].view,PyBUF_C_CONTIGUOUS|PyBUF_WRITABLE)<0) goto done;
        tiles[k].held=1; ntiles=k+1;
        tiles[k].ptr=tiles[k].view.buf; tiles[k].len=tiles[k].view.len;
      }
    }
    double sched_leaf=0.0;
    if(hmf_run_schedule(self,slots,oslots,self->nouts,svec,nsvec,tiles,(int)ntiles,parts,
                        &corr_seconds,&sched_leaf)) goto done;
    kernel+=sched_leaf;
  }
  /* the leaf steps the schedule does not run, by phase: modes, clusters, one batch */
  int nu=0;
  for(int i=0;i<ns;i++) if(self->steps[i].phase>=0) ui[nu++]=i;
  for(int p0=0;p0<nu;){
    int p1=p0+1;
    while(p1<nu && self->steps[ui[p1]].phase==self->steps[ui[p0]].phase) p1++;
    const int cnt=p1-p0;
    for(int k=p0;k<p1;k++) if(hmf_step_set_mode(&self->steps[ui[k]])) goto done;
    for(int k=p0;k<p1;k++){
      const int i=ui[k];
      const hmf_step *s=&self->steps[i]; const hmf_slot *sl=&slots[s->slot];
      const uintptr_t base=(uintptr_t)sl->ptr;
      const size_t step_b=(!s->real || s->stride==2)?8u:4u, width=s->real?4u:8u;
      const size_t nbytes=s->real?(s->stride==2?(size_t)(2*sl->samples-1)*4u:(size_t)sl->samples*4u)
                                 :(size_t)sl->samples*8u;
      const uintptr_t hi_read=base+((size_t)s->s_max+s->block_len-1)*step_b+width;
      spans[k-p0].lo=(base+(size_t)s->s_min*step_b)&~(uintptr_t)63;
      spans[k-p0].hi=(((base+nbytes)<hi_read?(base+nbytes):hi_read)+63)&~(uintptr_t)63;
      spans[k-p0].idx=k-p0;
    }
    qsort(spans,(size_t)cnt,sizeof(hmf_span),hmf_span_cmp);
    int nc=0, nm=0;
    clusters[0].members=members; clusters[0].count=1; members[nm++]=spans[0].idx;
    uintptr_t cur_end=spans[0].hi; nc=1;
    for(int k=1;k<cnt;k++){
      if(spans[k].lo<cur_end){
        clusters[nc-1].count++; members[nm++]=spans[k].idx;
        if(spans[k].hi>cur_end) cur_end=spans[k].hi;
      } else {
        clusters[nc].members=members+nm; clusters[nc].count=1; members[nm++]=spans[k].idx;
        cur_end=spans[k].hi; nc++;
      }
    }
    for(int c=0;c<nc;c++){
      qsort(clusters[c].members,(size_t)clusters[c].count,sizeof(int),hmf_int_cmp);
      clusters[c].first=clusters[c].members[0];
    }
    qsort(clusters,(size_t)nc,sizeof(hmf_cluster),hmf_cluster_cmp);
    int e=0;
    for(int c=0;c<nc;c++)
      for(int m=0;m<clusters[c].count;m++){
        const int i=ui[p0+clusters[c].members[m]];
        const hmf_step *s=&self->steps[i];
        hmf_job_bind(&jobs[p0+e],s,&slots[s->slot],0,s->nblocks,c);
        exec_of[i]=p0+e; e++;
      }
    for(int k=p0;k<p1;k++) self->steps[ui[k]].hmf->busy=1;
    int rc;
    const double t0=hmf_now();
    Py_BEGIN_ALLOW_THREADS
    rc=ap_hmf_run_series_batch_sparse(jobs+p0,cnt);
    Py_END_ALLOW_THREADS
    const double dt=hmf_now()-t0;
    for(int k=p0;k<p1;k++) self->steps[ui[k]].hmf->busy=0;
    if(rc<0){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done; }
    kernel+=dt;
    for(int k=p0;k<p1;k++){
      const int i=ui[k];
      seconds[i]=dt/(double)cnt; totals[i]=jobs[exec_of[i]].total;
      /* the step's batch time, pending in its plan's stats (MatchedFilter.performance_stats) */
      if(self->steps[i].has_stats){
        double *ps=self->steps[i].stats.buf; const double t=seconds[i];
        const int64_t kk=(int64_t)ps[0];
        ps[6+kk%256]=t; ps[1]+=t;
        if(!kk || t<ps[2]) ps[2]=t;
        if(!kk || t>ps[3]) ps[3]=t;
        ps[0]=(double)(kk+1);
      }
    }
    p0=p1;
  }
  /* the schedule's leaf steps: their slices' totals and seconds, one batch time a run */
  for(int i=0;i<ns;i++){
    if(self->steps[i].phase!=-1) continue;
    seconds[i]=parts[i].seconds; totals[i]=parts[i].total;
    if(self->steps[i].has_stats && parts[i].any){
      double *ps=self->steps[i].stats.buf; const double t=seconds[i];
      const int64_t kk=(int64_t)ps[0];
      ps[6+kk%256]=t; ps[1]+=t;
      if(!kk || t<ps[2]) ps[2]=t;
      if(!kk || t>ps[3]) ps[3]=t;
      ps[0]=(double)(kk+1);
    }
  }
  /* the flat steps, one ungated run each */
  for(int i=0;i<nf;i++){
    hmf_flat_step *f=&self->flats[i];
    double dt=0.0;
    f->mf->busy=1;
    const int frc=hmf_run_flat(f,&slots[f->slot],&fout[i],&dt);
    f->mf->busy=0;
    if(frc) goto done;
    kernel+=dt;
    seconds[ns+nsc+i]=dt; totals[ns+nsc+i]=fout[i].total;
    if(f->has_stats){
      double *ps=f->stats.buf;
      const int64_t k=(int64_t)ps[0];
      ps[6+k%256]=dt; ps[1]+=dt;
      if(!k || dt<ps[2]) ps[2]=dt;
      if(!k || dt>ps[3]) ps[3]=dt;
      ps[0]=(double)(k+1);
    }
  }
  /* assembly: per job its steps' peaks in step order, block-major (output rows), then the
     window-bin merges */
  Py_ssize_t total=0;
  for(int i=0;i<ns;i++)
    total+=(Py_ssize_t)(self->steps[i].phase==-1?parts[i].count:jobs[exec_of[i]].out_count);
  for(int i=0;i<nf;i++) total+=(Py_ssize_t)fout[i].count;
  total+=(Py_ssize_t)sing.kept;
  const size_t cap=total?(size_t)total:1;
  /* the arena's columns in one block, then the offsets */
  o_t=PyMem_Malloc(cap*5*8+((size_t)self->njobs+(size_t)nsc+1)*8);
  if(!o_t){ PyErr_NoMemory(); goto done; }
  o_s=(double*)(o_t+cap); o_v=(float*)(o_t+2*cap); o_bs=o_t+3*cap; o_bl=o_t+4*cap; offs=o_t+5*cap;
  if(self->njobs){
    keep=PyMem_Malloc(cap*sizeof(Py_ssize_t));
    if(!keep){ PyErr_NoMemory(); goto done; }
  }
  Py_ssize_t at=0; int i=0, fi=0;
  for(int j=0;j<self->njobs;j++){
    offs[j]=at;
    const Py_ssize_t job0=at;
    for(;i<ns && self->steps[i].job==j;i++){
      const hmf_step *s=&self->steps[i];
      if(s->phase==-1){
        /* its slices' peaks, joined in block order: mapped to output rows and sorted where
           the plan reorders its blocks or the slices ran out of block order */
        const hmf_parts *pt=&parts[i];
        if(!pt->total || !pt->count) continue;
        int64_t *ident=NULL;
        if(!s->order && !pt->monotone){
          ident=PyMem_Malloc((size_t)s->nblocks*8);
          if(!ident){ PyErr_NoMemory(); goto done; }
          for(int b=0;b<s->nblocks;b++) ident[b]=b;
        }
        at=hmf_append_peaks(o_t,o_s,o_v,o_bs,o_bl,at,s->tmap,s->ostarts,s->order?s->order:ident,
                            s->nt,(int64_t)s->nbins,s->block_len,(Py_ssize_t)pt->count,pt->flat,
                            pt->idx,pt->val);
        PyMem_Free(ident);
        if(at<0) goto done;
        continue;
      }
      const ap_hmf_sparse_job *jb=&jobs[exec_of[i]];
      const Py_ssize_t m=(Py_ssize_t)jb->out_count;
      if(!jb->total || !m) continue;
      at=hmf_append_peaks(o_t,o_s,o_v,o_bs,o_bl,at,s->tmap,s->ostarts,s->order,s->nt,
                          (int64_t)s->nbins,s->block_len,m,jb->out_flat,jb->out_idx,jb->out_val);
      if(at<0) goto done;
    }
    for(;fi<nf && self->flats[fi].job==j;fi++){
      const hmf_flat_step *f=&self->flats[fi]; const hmf_flat_out *fo=&fout[fi];
      if(!fo->total || !fo->count) continue;
      at=hmf_append_peaks(o_t,o_s,o_v,o_bs,o_bl,at,f->tmap,f->ostarts,NULL,f->nt,
                          (int64_t)f->nbins,f->block_len,(Py_ssize_t)fo->count,fo->flat,fo->idx,
                          fo->val);
      if(at<0) goto done;
    }
    const hmf_table_job *J=&self->jobs[j];
    at=hmf_job_merge(J->win_starts,J->nwin,J->merge_bs,J->nmerge,o_t,o_s,o_v,o_bs,o_bl,job0,at,keep,0);
    if(at<0) goto done;
  }
  {
    /* sample indices as int64, as FilterResults has them */
    int64_t *o_si=(int64_t*)o_s;
    hmf_samples_to_int(o_s,at);
    /* then each single-template call's peaks, as the follow-up kernel kept them */
    for(Py_ssize_t c=0;c<nsc;c++){
      const hmf_single *g=&self->singles[sing.single[c]];
      offs[self->njobs+c]=at;
      const int64_t gti=g->tmap[sing.row[c]];
      for(int64_t q=sing.offs[c];q<sing.offs[c+1];q++){
        o_t[at]=gti; o_si[at]=sing.si[q]; o_bs[at]=sing.bs[q]; o_bl[at]=(int64_t)g->n;
        o_v[2*at]=sing.snr[2*q]; o_v[2*at+1]=sing.snr[2*q+1];
        at++;
      }
      totals[ns+c]=(int)(sing.offs[c+1]-sing.offs[c]);
      seconds[ns+c]=sing.seconds/(double)nsc;
    }
  }
  offs[self->njobs+nsc]=at;
  ret=Py_BuildValue("(NNNNNNNNdd)",hmf_bytes(offs,((Py_ssize_t)self->njobs+nsc+1)*8),
                    hmf_bytes(o_t,at*8),hmf_bytes(o_s,at*8),hmf_bytes(o_v,at*8),
                    hmf_bytes(o_bs,at*8),hmf_bytes(o_bl,at*8),
                    hmf_bytes(totals,nout*(Py_ssize_t)sizeof(int)),
                    hmf_bytes(seconds,nout*8),kernel,corr_seconds);
done:
  hmf_single_out_free(&sing);
  if(parts) for(int k=0;k<ns;k++){ free(parts[k].flat); free(parts[k].idx); free(parts[k].val); }
  PyMem_Free(parts); PyMem_Free(ui);
  if(oslots) for(Py_ssize_t k=0;k<noslots;k++) if(oslots[k].held) PyBuffer_Release(&oslots[k].view);
  if(svec) for(Py_ssize_t k=0;k<nsvec;k++) PyBuffer_Release(&svec[k]);
  if(tiles) for(Py_ssize_t k=0;k<ntiles;k++) if(tiles[k].held) PyBuffer_Release(&tiles[k].view);
  PyMem_Free(oslots); PyMem_Free(svec); PyMem_Free(tiles);
  Py_XDECREF(oseq); Py_XDECREF(sseq); Py_XDECREF(tseq);
  if(jobs) for(int k=0;k<ns;k++){ free(jobs[k].out_flat); free(jobs[k].out_idx); free(jobs[k].out_val); }
  if(fout) for(int k=0;k<nf;k++){ free(fout[k].flat); free(fout[k].idx); free(fout[k].val); }
  PyMem_Free(fout);
  if(slots) for(int k=0;k<self->nslots;k++) if(slots[k].held) PyBuffer_Release(&slots[k].view);
  PyMem_Free(slots); PyMem_Free(jobs); PyMem_Free(spans); PyMem_Free(clusters); PyMem_Free(members);
  PyMem_Free(exec_of); PyMem_Free(totals); PyMem_Free(seconds);
  PyMem_Free(o_t); PyMem_Free(keep);
  Py_DECREF(seq);
  return ret;
}
/* run_corr(first, end, series, outputs, scales=None) -> seconds: correlation steps
   [first, end) on the series (one per slot), outputs (one per output slot) and scale vectors
   given: every step of a correlation call. */
static PyObject *HMFTable_run_corr(HMFTableObject *self,PyObject *args){
  int c0,c1; PyObject *series_arg,*outs_arg,*scales_arg=NULL;
  if(!PyArg_ParseTuple(args,"iiOO|O",&c0,&c1,&series_arg,&outs_arg,&scales_arg)) return NULL;
  if(c0<0 || c1<c0 || c1>self->ncorrs){
    PyErr_SetString(PyExc_ValueError,"HMFTable.run_corr: a step range is out of range"); return NULL;
  }
  double seconds;
  if(hmf_run_corrs(self,c0,c1,series_arg,outs_arg,scales_arg,&seconds)) return NULL;
  return PyFloat_FromDouble(seconds);
}
static PyObject *HMFTable_get_corrs(HMFTableObject *self,void *closure){
  (void)closure; return PyLong_FromLong(self->ncorrs);
}
static PyObject *HMFTable_get_steps(HMFTableObject *self,void *closure){
  (void)closure; return PyLong_FromLong(self->nsteps);
}
static PyObject *HMFTable_get_ops(HMFTableObject *self,void *closure){
  (void)closure; return PyLong_FromLong(self->nops);
}
static PyMethodDef HMFTable_methods[]={
  {"run",(PyCFunction)HMFTable_run,METH_VARARGS,
   "run(series, calls=(), outputs=None, scales=None) -> (offsets, templates, samples, snr, "
   "block_starts, block_lengths, step_totals, step_seconds, kernel_seconds, corr_seconds): every "
   "correlation step into the outputs (with the scale vectors), then every gated and flat step on "
   "its slot's series and every call (single, series, row, windows, binsize, aligned, threshold) "
   "bound to a single-template step, the peaks of each job (the table's, then one per call); "
   "totals and seconds per gated step, call, then flat step; the leaf kernels' and the "
   "correlation steps' seconds"},
  {"run_corr",(PyCFunction)HMFTable_run_corr,METH_VARARGS,
   "run_corr(first, end, series, outputs, scales=None) -> seconds: correlation "
   "steps [first, end) on the slots given"},
  {NULL,NULL,0,NULL}
};
static PyGetSetDef HMFTable_getset[]={
  {"steps",(getter)HMFTable_get_steps,NULL,"the number of steps",NULL},
  {"corrs",(getter)HMFTable_get_corrs,NULL,"the number of correlation steps",NULL},
  {"ops",(getter)HMFTable_get_ops,NULL,"the number of schedule ops (0: no schedule)",NULL},
  {NULL,NULL,NULL,NULL,NULL}
};
static PyTypeObject HMFTableType={
  PyVarObject_HEAD_INIT(NULL,0)
  .tp_name="matchedfilter._core.HMFTable", .tp_basicsize=sizeof(HMFTableObject),
  .tp_flags=Py_TPFLAGS_DEFAULT, .tp_new=PyType_GenericNew,
  .tp_init=(initproc)HMFTable_init, .tp_dealloc=(destructor)HMFTable_dealloc,
  .tp_methods=HMFTable_methods, .tp_getset=HMFTable_getset,
  .tp_doc="steps compiled once: HMFTable(steps, jobs, nslots, singles=(), flats=(), corrs=(), nouts=0)",
};

static PyObject *M_series_group(PyObject *self,PyObject *args){
  (void)self; Py_ssize_t n; int req;
  if(!PyArg_ParseTuple(args,"ni",&n,&req)) return NULL;
  if(n<1||req<1){ PyErr_SetString(PyExc_ValueError,"n and the requested group must be positive"); return NULL; }
  return PyLong_FromLong(ap_hmf_effective_group((size_t)n,req));
}
void ap_gauss_fill(float *out, size_t n, uint64_t seed, uint64_t offset);   /* src/gauss.cc */
void ap_gauss_fill_rows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                        uint64_t offset, uint64_t step, const float *scale,
                        const unsigned char *keep);
/* vulkan_emit(cmd, fns, ops, start, end): the Vulkan emitter of the shared command list
   (_gpuhost.CommandList): record ops[start:end) into command buffer cmd. ops is a list's
   operations resolved to Vulkan (_vkcompute._VkNative): an opcode, then its integer
   arguments (handles, words, barrier fields); fns holds the address of each opcode's entry
   point. Returns the index past the last op recorded, or -1 on an unknown opcode. */
typedef struct { uint32_t sType; const void *pNext; uint32_t src, dst; } vk_mem_barrier;
typedef struct { uint32_t sType; const void *pNext; uint32_t src, dst, src_qf, dst_qf;
                 uint64_t buffer, offset, size; } vk_buf_barrier;
typedef void (*vk_bind_pipeline_fn)(void*, uint32_t, uint64_t);
typedef void (*vk_bind_sets_fn)(void*, uint32_t, uint64_t, uint32_t, uint32_t, const uint64_t*,
                                uint32_t, const uint32_t*);
typedef void (*vk_push_fn)(void*, uint64_t, uint32_t, uint32_t, uint32_t, const void*);
typedef void (*vk_dispatch_fn)(void*, uint32_t, uint32_t, uint32_t);
typedef void (*vk_dispatch_indirect_fn)(void*, uint64_t, uint64_t);
typedef void (*vk_fill_fn)(void*, uint64_t, uint64_t, uint64_t, uint32_t);
typedef void (*vk_update_fn)(void*, uint64_t, uint64_t, uint64_t, const void*);
typedef void (*vk_barrier_fn)(void*, uint32_t, uint32_t, uint32_t, uint32_t, const void*,
                              uint32_t, const void*, uint32_t, const void*);
static Py_ssize_t vulkan_emit_ops(void *cmd, const uint64_t *fn, const uint64_t *op, size_t start,
                              size_t end){
  size_t i=start;
  while(i<end){
    switch(op[i]){
    case 1: ((vk_bind_pipeline_fn)(uintptr_t)fn[1])(cmd,(uint32_t)op[i+1],op[i+2]); i+=3; break;
    case 2: { const uint64_t set=op[i+3];
      ((vk_bind_sets_fn)(uintptr_t)fn[2])(cmd,(uint32_t)op[i+1],op[i+2],0,1,&set,0,NULL); i+=4; break; }
    case 3: { uint32_t w[64]; const size_t nw=(size_t)op[i+5];
      if(nw>64) return -1;
      for(size_t k=0;k<nw;k++) w[k]=(uint32_t)op[i+6+k];
      ((vk_push_fn)(uintptr_t)fn[3])(cmd,op[i+1],(uint32_t)op[i+2],(uint32_t)op[i+3],
                                     (uint32_t)op[i+4],w);
      i+=6+nw; break; }
    case 4: ((vk_dispatch_fn)(uintptr_t)fn[4])(cmd,(uint32_t)op[i+1],(uint32_t)op[i+2],
                                               (uint32_t)op[i+3]); i+=4; break;
    case 5: ((vk_dispatch_indirect_fn)(uintptr_t)fn[5])(cmd,op[i+1],op[i+2]); i+=3; break;
    case 6: ((vk_fill_fn)(uintptr_t)fn[6])(cmd,op[i+1],op[i+2],op[i+3],(uint32_t)op[i+4]);
      i+=5; break;
    case 7: ((vk_update_fn)(uintptr_t)fn[7])(cmd,op[i+1],op[i+2],op[i+3],
                                             (const void*)(uintptr_t)op[i+4]); i+=5; break;
    case 8: { vk_mem_barrier mb={46,NULL,(uint32_t)op[i+4],(uint32_t)op[i+5]};
      ((vk_barrier_fn)(uintptr_t)fn[8])(cmd,(uint32_t)op[i+1],(uint32_t)op[i+2],(uint32_t)op[i+3],
                                        1,&mb,0,NULL,0,NULL); i+=6; break; }
    case 9: { vk_buf_barrier bb={44,NULL,(uint32_t)op[i+4],(uint32_t)op[i+5],(uint32_t)op[i+6],
                                 (uint32_t)op[i+7],op[i+8],op[i+9],op[i+10]};
      ((vk_barrier_fn)(uintptr_t)fn[8])(cmd,(uint32_t)op[i+1],(uint32_t)op[i+2],(uint32_t)op[i+3],
                                        0,NULL,1,&bb,0,NULL); i+=11; break; }
    case 10: ((vk_barrier_fn)(uintptr_t)fn[8])(cmd,(uint32_t)op[i+1],(uint32_t)op[i+2],
                                               (uint32_t)op[i+3],0,NULL,0,NULL,0,NULL); i+=4; break;
    default: return -1;
    }
  }
  return (Py_ssize_t)i;
}
static PyObject *M_vulkan_emit(PyObject *self,PyObject *args){
  (void)self; unsigned long long cmd; PyObject *fo, *oo; Py_ssize_t start, end;
  if(!PyArg_ParseTuple(args,"KOOnn",&cmd,&fo,&oo,&start,&end)) return NULL;
  Py_buffer f, o;
  if(PyObject_GetBuffer(fo,&f,PyBUF_C_CONTIGUOUS)<0) return NULL;
  if(PyObject_GetBuffer(oo,&o,PyBUF_C_CONTIGUOUS)<0){ PyBuffer_Release(&f); return NULL; }
  Py_ssize_t r=-1;
  if(f.itemsize==8 && o.itemsize==8 && f.len>=9*8 && start>=0 && start<=end && end*8<=o.len)
    r=vulkan_emit_ops((void*)(uintptr_t)cmd,(const uint64_t*)f.buf,(const uint64_t*)o.buf,
                  (size_t)start,(size_t)end);
  PyBuffer_Release(&f); PyBuffer_Release(&o);
  if(r<0){ PyErr_SetString(PyExc_ValueError,"vulkan_emit: bad ops, range or entry-point table"); return NULL; }
  return PyLong_FromSsize_t(r);
}

/* One float32's bits as IEEE half bits, exactly as NumPy's float32 -> float16 cast
   (npy_floatbits_to_halfbits, NumPy's halffloat.c): round to nearest, ties to even;
   subnormal halves; overflow to a signed infinity; a NaN stays a NaN with its sign and the
   top of its payload. Portable C, so every ISA gives these bits. */
static inline uint16_t half_bits_of(uint32_t f){
  const uint16_t h_sgn=(uint16_t)((f&0x80000000u)>>16);
  uint32_t f_exp=f&0x7f800000u, f_sig;
  if(f_exp>=0x47800000u){                      /* overflow, infinity or NaN */
    if(f_exp==0x7f800000u){
      f_sig=f&0x007fffffu;
      if(f_sig!=0){
        uint16_t ret=(uint16_t)(0x7c00u+(f_sig>>13));
        if(ret==0x7c00u) ret++;                /* stays a NaN */
        return (uint16_t)(h_sgn+ret);
      }
      return (uint16_t)(h_sgn+0x7c00u);
    }
    return (uint16_t)(h_sgn+0x7c00u);
  }
  if(f_exp<=0x38000000u){                      /* a subnormal half or a signed zero */
    if(f_exp<0x33000000u) return h_sgn;
    f_exp>>=23;
    f_sig=0x00800000u+(f&0x007fffffu);
    f_sig>>=(113-f_exp);
    if(((f_sig&0x00003fffu)!=0x00001000u) || (f&0x000007ffu)) f_sig+=0x00001000u;
    return (uint16_t)(h_sgn+(uint16_t)(f_sig>>13));
  }
  {
    const uint16_t h_exp=(uint16_t)((f_exp-0x38000000u)>>13);
    f_sig=f&0x007fffffu;
    if((f_sig&0x00003fffu)!=0x00001000u) f_sig+=0x00001000u;
    /* a carry out of the significand moves into the exponent, to infinity at the top */
    return (uint16_t)(h_sgn+(uint16_t)((uint16_t)(f_sig>>13)+h_exp));
  }
}

/* half_bits(src, dst): dst[i] = src[i] as IEEE half bits, NumPy's float32 -> float16 cast;
   src a C-contiguous float32 buffer, dst a writable C-contiguous 16-bit buffer as long. */
static PyObject *M_half_bits(PyObject *self,PyObject *args){
  (void)self; PyObject *so, *dout;
  if(!PyArg_ParseTuple(args,"OO",&so,&dout)) return NULL;
  Py_buffer s, d;
  if(PyObject_GetBuffer(so,&s,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return NULL;
  if(PyObject_GetBuffer(dout,&d,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS)<0){ PyBuffer_Release(&s); return NULL; }
  if(!s.format || strcmp(s.format,"f")!=0 || s.itemsize!=4 || d.itemsize!=2 || d.len*2!=s.len){
    PyBuffer_Release(&s); PyBuffer_Release(&d);
    PyErr_SetString(PyExc_TypeError,"half_bits needs float32 src and a 16-bit dst of as many items");
    return NULL;
  }
  const uint32_t *src=(const uint32_t*)s.buf; uint16_t *dst=(uint16_t*)d.buf;
  const size_t n=(size_t)(s.len/4);
  Py_BEGIN_ALLOW_THREADS
  for(size_t i=0;i<n;i++) dst[i]=half_bits_of(src[i]);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&s); PyBuffer_Release(&d);
  Py_RETURN_NONE;
}
/* xxh64(buffer, seed=0) -> int: XXH64 (Yann Collet's xxHash, 64-bit, as specified) of a
   C-contiguous buffer's bytes, at memory speed; the device root's check that a block's
   array still holds what its device copy was made from (_gpuroot). Every word is mixed at
   its position, so permuted or cancelling changes change it. */
#define XXP1 11400714785074694791ULL
#define XXP2 14029467366897019727ULL
#define XXP3 1609587929392839161ULL
#define XXP4 9650029242287828579ULL
#define XXP5 2870177450012600261ULL
static inline uint64_t xx_rotl(uint64_t x,int r){ return (x<<r)|(x>>(64-r)); }
static inline uint64_t xx_rd64(const unsigned char *p){ uint64_t v; memcpy(&v,p,8);
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
  v=__builtin_bswap64(v);
#endif
  return v; }
static inline uint32_t xx_rd32(const unsigned char *p){ uint32_t v; memcpy(&v,p,4);
#if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
  v=__builtin_bswap32(v);
#endif
  return v; }
static inline uint64_t xx_round(uint64_t acc,uint64_t in){ acc+=in*XXP2; acc=xx_rotl(acc,31); return acc*XXP1; }
static inline uint64_t xx_merge(uint64_t acc,uint64_t v){ acc^=xx_round(0,v); return acc*XXP1+XXP4; }
static uint64_t xxh64(const unsigned char *p,size_t len,uint64_t seed){
  const unsigned char *end=p+len; uint64_t h;
  if(len>=32){
    const unsigned char *lim=end-32;
    uint64_t v1=seed+XXP1+XXP2, v2=seed+XXP2, v3=seed, v4=seed-XXP1;
    do{ v1=xx_round(v1,xx_rd64(p)); v2=xx_round(v2,xx_rd64(p+8));
        v3=xx_round(v3,xx_rd64(p+16)); v4=xx_round(v4,xx_rd64(p+24)); p+=32; }while(p<=lim);
    h=xx_rotl(v1,1)+xx_rotl(v2,7)+xx_rotl(v3,12)+xx_rotl(v4,18);
    h=xx_merge(h,v1); h=xx_merge(h,v2); h=xx_merge(h,v3); h=xx_merge(h,v4);
  } else h=seed+XXP5;
  h+=(uint64_t)len;
  while(p+8<=end){ h^=xx_round(0,xx_rd64(p)); h=xx_rotl(h,27)*XXP1+XXP4; p+=8; }
  if(p+4<=end){ h^=(uint64_t)xx_rd32(p)*XXP1; h=xx_rotl(h,23)*XXP2+XXP3; p+=4; }
  while(p<end){ h^=(*p)*XXP5; h=xx_rotl(h,11)*XXP1; p++; }
  h^=h>>33; h*=XXP2; h^=h>>29; h*=XXP3; h^=h>>32;
  return h;
}
static PyObject *M_xxh64(PyObject *self,PyObject *args){
  (void)self; PyObject *o; unsigned long long seed=0;
  if(!PyArg_ParseTuple(args,"O|K",&o,&seed)) return NULL;
  Py_buffer b;
  if(PyObject_GetBuffer(o,&b,PyBUF_C_CONTIGUOUS)<0) return NULL;
  uint64_t h;
  Py_BEGIN_ALLOW_THREADS
  h=xxh64((const unsigned char*)b.buf,(size_t)b.len,(uint64_t)seed);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b);
  return PyLong_FromUnsignedLongLong((unsigned long long)h);
}
static PyObject *M_gauss_fill(PyObject *self,PyObject *args){
  PyObject *o; unsigned long long seed, offset;
  if(!PyArg_ParseTuple(args,"OKK",&o,&seed,&offset)) return NULL;
  Py_buffer b;
  if(PyObject_GetBuffer(o,&b,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return NULL;
  if(!b.format || strcmp(b.format,"f")!=0 || b.itemsize!=4){
    PyBuffer_Release(&b); PyErr_SetString(PyExc_TypeError,"gauss_fill needs a C-contiguous float32 buffer"); return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  ap_gauss_fill((float*)b.buf,(size_t)(b.len/4),(uint64_t)seed,(uint64_t)offset);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b);
  Py_RETURN_NONE;
}
/* gauss_fill_rows(out, seed, offset, step, scale=None, keep=None): out float32 (rows, len)
   C-contiguous, out[r, i] = draw offset + r * step + i of stream seed, times scale[i // 2]
   (float32, at least (len + 1) // 2 of them) when given; with keep (a byte a row) only the
   rows with a nonzero byte are written: simulate's fill (ap_gauss_fill_rows). */
static PyObject *M_gauss_fill_rows(PyObject *self,PyObject *args){
  (void)self; PyObject *o, *so=Py_None, *ko=Py_None; unsigned long long seed, offset, step;
  if(!PyArg_ParseTuple(args,"OKKK|OO",&o,&seed,&offset,&step,&so,&ko)) return NULL;
  Py_buffer b, sb={0}, kb={0}; int has_scale = so!=Py_None, has_keep = ko!=Py_None;
  if(PyObject_GetBuffer(o,&b,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|PyBUF_ND)<0) return NULL;
  if(has_scale && PyObject_GetBuffer(so,&sb,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&b); return NULL; }
  if(has_keep && PyObject_GetBuffer(ko,&kb,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){
    PyBuffer_Release(&b); if(has_scale) PyBuffer_Release(&sb); return NULL;
  }
  const Py_ssize_t rows = b.ndim==2 ? b.shape[0] : 0, len = b.ndim==2 ? b.shape[1] : 0;
  if(!b.format || strcmp(b.format,"f")!=0 || b.itemsize!=4 || b.ndim!=2
     || (has_scale && (!sb.format || strcmp(sb.format,"f")!=0 || sb.itemsize!=4 || sb.len/4 < (len+1)/2))
     || (has_keep && (kb.itemsize!=1 || kb.len!=rows))){
    PyBuffer_Release(&b); if(has_scale) PyBuffer_Release(&sb); if(has_keep) PyBuffer_Release(&kb);
    PyErr_SetString(PyExc_TypeError,"gauss_fill_rows needs a C-contiguous float32 (rows, len) buffer, a float32 scale of (len + 1) // 2 or more and a one-byte keep per row");
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  ap_gauss_fill_rows((float*)b.buf,(size_t)len,(size_t)rows,(size_t)len,(uint64_t)seed,(uint64_t)offset,
                          (uint64_t)step,has_scale ? (const float*)sb.buf : NULL,
                          has_keep ? (const unsigned char*)kb.buf : NULL);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b); if(has_scale) PyBuffer_Release(&sb); if(has_keep) PyBuffer_Release(&kb);
  Py_RETURN_NONE;
}
/* A[e] = |g y[e] + d[e]|^2 for e < m (d NULL: |g y[e]|^2), y and d complex: simulate's
   statistics, under Highway's dispatch (src/records.cc). Returns the largest A. */
float ap_sim_power(const float *y, const float *d, float g, long long m, float *A);
/* One statistic's running-maximum records outward from the signal (simulate): of the
   values a[e0], a[e0 + dir], ... (L of them), each exceeding all before it (the first always)
   as (distance i + d0 for the i-th, sqrt value), appended at pos[*k], val[*k] and *k advanced
   (src/records.cc). Returns 0, or -1 when the arrays (cap entries) are full. */
int ap_sim_records(const float *a, long long e0, int dir, long long L, long long d0,
                   int32_t *pos, float *val, long long *k, long long cap);
void ap_sim_twiddle(const float *x, const float *tw, size_t m, float *out);
void ap_sim_interleave_complex(const float *even_c, const float *odd_c, size_t m, float *out);
/* running_records(a, e0, dir, L, d0, pos, val): ap_sim_records over a (float32, non-negative)
   into pos (int32) and val (float32, pos's length) from their start: the record count, or -1
   when they are too short (simulate's records, for the tests). */
static PyObject *M_running_records(PyObject *self,PyObject *args){
  (void)self; PyObject *ao,*po,*vo; long long e0,L,d0; int dir;
  if(!PyArg_ParseTuple(args,"OLiLLOO",&ao,&e0,&dir,&L,&d0,&po,&vo)) return NULL;
  Py_buffer ab,pb,vb;
  if(PyObject_GetBuffer(ao,&ab,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return NULL;
  if(PyObject_GetBuffer(po,&pb,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&ab); return NULL; }
  if(PyObject_GetBuffer(vo,&vb,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&ab); PyBuffer_Release(&pb); return NULL; }
  const long long na=ab.len/4;
  const int ok = ab.itemsize==4 && strcmp(ab.format,"f")==0 && pb.itemsize==4 && (strcmp(pb.format,"i")==0||strcmp(pb.format,"l")==0)
                 && vb.itemsize==4 && strcmp(vb.format,"f")==0 && pb.len==vb.len && (dir==1||dir==-1) && L>=0
                 && e0>=0 && e0<na+(L==0) && (L==0 || (dir>0 ? e0+L<=na : e0-L>=-1));
  long long k=0; int r=0;
  if(ok){
    Py_BEGIN_ALLOW_THREADS
    r=ap_sim_records((const float*)ab.buf,e0,dir,L,d0,(int32_t*)pb.buf,(float*)vb.buf,&k,pb.len/4);
    Py_END_ALLOW_THREADS
  }
  PyBuffer_Release(&ab); PyBuffer_Release(&pb); PyBuffer_Release(&vb);
  if(!ok){ PyErr_SetString(PyExc_ValueError,"running_records: a float32, dir +-1, the L values from e0 inside a; pos int32 and val float32 of one length"); return NULL; }
  return PyLong_FromLongLong(r<0 ? -1 : k);
}
/* Buffers of a records output tuple (simulate): per entry pos int32, val float32 of one
   length and off int64 (nrows + 1). Returns how many were taken
   (all on success; the caller releases that many). */
static int sr_take(PyObject *po,PyObject *vo,PyObject *oo,Py_ssize_t want,long long nrows,
                   Py_buffer *pb,Py_buffer *vb,Py_buffer *ob,int *ok){
  int got=0;
  if(!PyTuple_Check(po)||!PyTuple_Check(vo)||!PyTuple_Check(oo)||PyTuple_GET_SIZE(po)!=want||PyTuple_GET_SIZE(vo)!=want||PyTuple_GET_SIZE(oo)!=want){ *ok=0; return 0; }
  for(Py_ssize_t s=0;s<want;s++){
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(po,s),&pb[s],PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ *ok=0; break; }
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(vo,s),&vb[s],PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&pb[s]); *ok=0; break; }
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(oo,s),&ob[s],PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&pb[s]); PyBuffer_Release(&vb[s]); *ok=0; break; }
    got=(int)s+1;
    if(!(pb[s].itemsize==4 && (strcmp(pb[s].format,"i")==0||strcmp(pb[s].format,"l")==0) && vb[s].itemsize==4 && strcmp(vb[s].format,"f")==0
         && pb[s].len==vb[s].len && ob[s].itemsize==8 && (strcmp(ob[s].format,"q")==0||strcmp(ob[s].format,"l")==0) && ob[s].len/8==nrows+1)){ *ok=0; break; }
  }
  return got;
}
static PyObject *M_simulate(PyObject *self,PyObject *args){
  (void)self;
  PyObject *sco,*bo,*bso,*tbo,*to,*fio,*spo,*svo,*soo,*npo,*nvo,*noo,*k0o=Py_None,*alo=Py_None,*kmo=Py_None;
  unsigned long long seed; long long row0,nrows,kmax; double fscale, keep_at=0.0;
  if(!PyArg_ParseTuple(args,"OKLLLOOdOOOOOOOOO|dOOO",&sco,&seed,&row0,&nrows,&kmax,&bo,&bso,&fscale,&tbo,&to,&fio,&spo,&svo,&soo,&npo,&nvo,&noo,&keep_at,&k0o,&alo,&kmo)) return NULL;
  if(!PyTuple_Check(bo)||!PyTuple_Check(bso)){ PyErr_SetString(PyExc_TypeError,"simulate: bands and bscale must be tuples"); return NULL; }
  const Py_ssize_t nb=PyTuple_GET_SIZE(bo), ns=2*(1+nb);
  const int has_sig = tbo!=Py_None, has_noise = npo!=Py_None, skip_fine = kmo!=Py_None;
  if(nb<1||nb>31||PyTuple_GET_SIZE(bso)!=nb||nrows<1||row0<0||!(has_sig||has_noise)||(skip_fine&&!has_sig)){
    PyErr_SetString(PyExc_ValueError,"simulate: one bscale per band, 1..31 bands, nrows >= 1, row0 >= 0, signal or noise outputs"); return NULL;
  }
  long long b[32], k0[32]={0}, khi[32]={0}; float bs[32], al[32], be[32]; int any_k0=0, any_alpha=0;
  for(Py_ssize_t i=0;i<32;i++){ al[i]=1.f; be[i]=0.f; }
  for(Py_ssize_t i=0;i<nb;i++){ b[i]=PyLong_AsLongLong(PyTuple_GET_ITEM(bo,i)); bs[i]=(float)PyFloat_AsDouble(PyTuple_GET_ITEM(bso,i)); }
  if(k0o!=Py_None){
    if(!PyTuple_Check(k0o)){ PyErr_SetString(PyExc_TypeError,"simulate: k0s must be a tuple"); return NULL; }
    if(PyTuple_GET_SIZE(k0o)!=nb){ PyErr_SetString(PyExc_ValueError,"simulate: one k0 per band"); return NULL; }
    for(Py_ssize_t i=0;i<nb;i++){
      k0[i]=PyLong_AsLongLong(PyTuple_GET_ITEM(k0o,i));
      if(k0[i]>0) any_k0=1;
    }
  }
  if(alo!=Py_None){
    if(!PyTuple_Check(alo)){ PyErr_SetString(PyExc_TypeError,"simulate: alphas must be a tuple"); return NULL; }
    if(PyTuple_GET_SIZE(alo)!=nb){ PyErr_SetString(PyExc_ValueError,"simulate: one alpha per band"); return NULL; }
    for(Py_ssize_t i=0;i<nb;i++){
      double av=PyFloat_AsDouble(PyTuple_GET_ITEM(alo,i));
      if(!(av>0.0 && av<=1.0)){
        if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"simulate: alphas must lie in (0, 1]");
        return NULL;
      }
      al[i]=(float)av;
      be[i]=av<1.0 ? (float)sqrt(1.0 - av*av) : 0.f;
      if(al[i]<1.f) any_alpha=1;
    }
  }
  if(PyErr_Occurred()) return NULL;
  Py_buffer sc,tb={0},tt={0},fib={0},kmb={0}; int gin=0, got_km=0, ok=1;
  Py_buffer *in[4]={&sc,&tb,&tt,&fib}; PyObject *io[4]={sco,tbo,to,fio};
  for(;gin<(has_sig?4:1);gin++) if(PyObject_GetBuffer(io[gin],in[gin],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ ok=0; break; }
  if(ok && skip_fine){
    if(PyObject_GetBuffer(kmo,&kmb,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0;
    else { got_km=1; ok = (kmb.itemsize==1 && kmb.len==nrows); }
  }
  Py_buffer spb[64],svb[64],sob[64],npb[32],nvb[32],nob[32]; int sgot=0, ngot=0;
  if(ok && has_sig) sgot=sr_take(spo,svo,soo,ns,nrows,spb,svb,sob,&ok);
  if(ok && has_noise) ngot=sr_take(npo,nvo,noo,nb,nrows,npb,nvb,nob,&ok);
  const long long n = ok ? sc.len/4 : 0;
  ok = ok && sc.itemsize==4 && strcmp(sc.format,"f")==0 && n>=2 && n<=(1<<24) && kmax>=1 && kmax<=n;
  long long NF=0;
  if(ok && has_sig){
    ok = tb.itemsize==8 && strcmp(tb.format,"Zf")==0 && tb.len/8 % ((1+nb)*n)==0
         && tt.itemsize==8 && (strcmp(tt.format,"q")==0||strcmp(tt.format,"l")==0) && tt.len/8==nrows
         && fib.itemsize==4 && (strcmp(fib.format,"i")==0||strcmp(fib.format,"l")==0) && fib.len/4==nrows;
    NF = ok ? tb.len/8/((1+nb)*n) : 0;
  }
  long long max_band_hi=0;
  for(Py_ssize_t i=0;i<nb && ok;i++){
    ok = b[i]>=1 && b[i]<=n && n%b[i]==0 && (i==0||b[i]>b[i-1]) && b[i]<=32768
         && k0[i]>=0 && (k0[i]==0 || k0[i]<n/2);
    if(ok){
      khi[i] = k0[i]==0 ? b[i] : (k0[i]+b[i] < n/2 ? k0[i]+b[i] : n/2);
      if(khi[i] > max_band_hi) max_band_hi = khi[i];
    }
  }
  if(ok && has_sig){
    const int *fi=(const int*)fib.buf; const long long *t=(const long long*)tt.buf;
    for(long long r=0;r<nrows;r++) if(fi[r]<0||fi[r]>=NF||t[r]<0||t[r]>=n){ ok=0; break; }
  }
  #define SIM_RELEASE() do{ \
    for(int s=0;s<sgot;s++){ PyBuffer_Release(&spb[s]); PyBuffer_Release(&svb[s]); PyBuffer_Release(&sob[s]); } \
    for(int s=0;s<ngot;s++){ PyBuffer_Release(&npb[s]); PyBuffer_Release(&nvb[s]); PyBuffer_Release(&nob[s]); } \
    if(got_km) PyBuffer_Release(&kmb); \
    for(int i=0;i<gin;i++) PyBuffer_Release(in[i]); }while(0)
  if(!ok){
    SIM_RELEASE();
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError,"simulate: scale float32 (n), 1 <= kmax <= n; bands ascending, dividing n, <= 32768; with a signal tab complex64 (NF, 1 + bands, n), t int64 in [0, n), fi int32 in [0, NF) (nrows), pos int32 per statistic and side, and per band for the noise; val float32 of pos's length, off int64 (nrows + 1)");
    return NULL;
  }
  ap_sim sim; memset(&sim,0,sizeof sim);
  ap_sim_out sig_out[64], noise_out[32];
  sim.scale=(const float*)sc.buf; sim.n=n; sim.kmax=kmax; sim.row0=row0; sim.nrows=nrows;
  sim.seed=(uint64_t)seed; sim.nb=nb; sim.max_band_hi=max_band_hi;
  memcpy(sim.b,b,sizeof b); memcpy(sim.k0,k0,sizeof k0); memcpy(sim.khi,khi,sizeof khi);
  memcpy(sim.bs,bs,sizeof bs); memcpy(sim.al,al,sizeof al); memcpy(sim.be,be,sizeof be);
  sim.any_k0=any_k0; sim.any_alpha=any_alpha; sim.fscale=fscale; sim.keep_at=keep_at;
  if(has_sig){
    sim.tab=(const float*)tb.buf; sim.t=(const long long*)tt.buf; sim.fi=(const int*)fib.buf;
    for(Py_ssize_t q=0;q<ns;q++)
      sig_out[q]=(ap_sim_out){(int32_t*)spb[q].buf,(float*)svb[q].buf,(long long*)sob[q].buf,svb[q].len/4};
    sim.sig=sig_out;
  }
  if(skip_fine) sim.km=(const unsigned char*)kmb.buf;
  if(has_noise){
    for(Py_ssize_t q=0;q<nb;q++)
      noise_out[q]=(ap_sim_out){(int32_t*)npb[q].buf,(float*)nvb[q].buf,(long long*)nob[q].buf,nvb[q].len/4};
    sim.noise=noise_out;
  }
  const int ready = ap_sim_setup(&sim)==0;
  if(ready){
    Py_BEGIN_ALLOW_THREADS
    ap_sim_run(&sim);
    Py_END_ALLOW_THREADS
  }
  ap_sim_free(&sim);
  SIM_RELEASE();
  #undef SIM_RELEASE
  if(!ready){ PyErr_SetString(PyExc_MemoryError,"simulate: no FFT plan or buffer"); return NULL; }
  PyObject *so=Py_None, *no=Py_None; Py_INCREF(Py_None); Py_INCREF(Py_None);
  if(has_sig){ Py_DECREF(so); so=PyTuple_New(ns); for(Py_ssize_t q=0;q<ns;q++) PyTuple_SET_ITEM(so,q,PyLong_FromLongLong(sim.ks[q])); }
  if(has_noise){ Py_DECREF(no); no=PyTuple_New(nb); for(Py_ssize_t q=0;q<nb;q++) PyTuple_SET_ITEM(no,q,PyLong_FromLongLong(sim.kn[q])); }
  return Py_BuildValue("(NNL)",so,no,sim.done);
}
/* records_within(pos, val, off, reach, out, at=None): per row r of records (pos int32, val
   float32, off int64 (rows + 1), row r's at [off[r], off[r + 1]), rising in pos and val), into
   out (float32, rows) the value of its last record at pos <= reach[r] (int64), 0 where none is,
   and into at (int32, rows) when given that record's pos, -1 where none is: the largest
   statistic within reach of a running maximum's start and where it lies (gatechain). */
static PyObject *M_records_within(PyObject *self,PyObject *args){
  (void)self; PyObject *po,*vo,*oo,*ro,*out,*ato=Py_None;
  if(!PyArg_ParseTuple(args,"OOOOO|O",&po,&vo,&oo,&ro,&out,&ato)) return NULL;
  Py_buffer abuf={0}; int has_at = ato!=Py_None;
  if(has_at){
    if(PyObject_GetBuffer(ato,&abuf,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return NULL;
  }
  Py_buffer pb,vb,ob,rb,xb; Py_buffer *bs[5]={&pb,&vb,&ob,&rb,&xb}; PyObject *os[5]={po,vo,oo,ro,out}; int got=0;
  for(;got<5;got++) if(PyObject_GetBuffer(os[got],bs[got],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|(got==4?PyBUF_WRITABLE:0))<0) break;
  const long long rows = got==5 ? rb.len/8 : 0;
  int ok = got==5 && pb.itemsize==4 && (strcmp(pb.format,"i")==0||strcmp(pb.format,"l")==0) && vb.itemsize==4 && strcmp(vb.format,"f")==0
           && pb.len==vb.len && ob.itemsize==8 && (strcmp(ob.format,"q")==0||strcmp(ob.format,"l")==0) && ob.len/8==rows+1
           && rb.itemsize==8 && (strcmp(rb.format,"q")==0||strcmp(rb.format,"l")==0) && xb.itemsize==4 && strcmp(xb.format,"f")==0 && xb.len/4==rows
           && (!has_at || (abuf.itemsize==4 && (strcmp(abuf.format,"i")==0||strcmp(abuf.format,"l")==0) && abuf.len/4==rows));
  if(ok){
    const long long *off=(const long long*)ob.buf, nrec=pb.len/4;
    ok = off[0]>=0 && off[rows]<=nrec;
    for(long long r=0;r<rows && ok;r++) ok = off[r]<=off[r+1];
  }
  if(ok){
    const int32_t *pos=(const int32_t*)pb.buf; const float *val=(const float*)vb.buf;
    const long long *off=(const long long*)ob.buf, *reach=(const long long*)rb.buf; float *o=(float*)xb.buf;
    int32_t *at = has_at ? (int32_t*)abuf.buf : NULL;
    Py_BEGIN_ALLOW_THREADS
    for(long long r=0;r<rows;r++){
      float v=0.f; int32_t a=-1;
      for(long long i=off[r];i<off[r+1] && pos[i]<=reach[r];i++){ v=val[i]; a=pos[i]; }
      o[r]=v;
      if(at) at[r]=a;
    }
    Py_END_ALLOW_THREADS
  }
  for(int i=0;i<got;i++) PyBuffer_Release(bs[i]);
  if(has_at) PyBuffer_Release(&abuf);
  if(!ok){ if(!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError,"records_within: pos int32 and val float32 of one length, off int64 (rows + 1) ascending within them, reach int64 (rows), out float32 (rows)"); return NULL; }
  Py_RETURN_NONE;
}
/* gatechain._chain_candidates's search (see there): every split it considers, in its
   depth-first order, as (earlier thresholds, earlier reach, lasts). S (M, k) float32: the
   search half's coarse maxima of the chain's tiers; Nc (k, R) float32: the noise blocks the
   search can keep alive, by tier; low[i], lowv[i] (i < k - 1): tier i's K + 1 smallest
   detection indices and values, ascending; lasto, lastv: the last tier's; splits: the budget
   shares tried per tier; dsets: per candidate half-width, the detections its window misses
   (int64 indices), dismissed whatever the tiers. lasts holds per set (last threshold, its
   reach) or None. A reach is the alive count over Nn as a double, the same float as
   Python's int division. */
typedef struct {
  int k, K, M, R, nsplit, prune; long long Nn; double useless;
  const float *S, *Nc; const long long *low[3]; const float *lowv[3];
  const long long *lasto; const float *lastv; int nlast; const double *splits;
  int nsets; const long long **dset; const Py_ssize_t *dlen;
  unsigned char *dead; int *alive[4]; PyObject *out; int err;
} cc_state;

/* Noise blocks of tier's column at or above g among alive (n of them; NULL: all R), written
   to store when given; their count. Index lists: past the first tier few blocks are alive,
   and a node then reads only those. */
static int cc_filter(const cc_state *c, int tier, float g, const int *alive, int n, int *store){
  const float *col=c->Nc+(size_t)tier*c->R; int m=0;
  if(alive){
    if(store){ for(int j=0;j<n;j++){ const int r=alive[j]; store[m]=r; m+=col[r]>=g; } }
    else     { for(int j=0;j<n;j++) m+=col[alive[j]]>=g; }
  } else {
    const int R=c->R;
    if(store){ for(int r=0;r<R;r++){ store[m]=r; m+=col[r]>=g; } }
    else     { for(int r=0;r<R;r++) m+=col[r]>=g; }
  }
  return m;
}

/* The window's misses carry this mark while a set is applied: the tiers' are 1 .. k - 1. */
#define CC_WINDOW 255

static void cc_consider(cc_state *c, const double *prefix, int ndead, const int *alive, int nalive,
                        const double *fracs){
  if(c->prune) for(int i=0;i<c->k-1;i++) if(fracs[i]>c->useless) return;
  PyObject *lasts=PyTuple_New(c->nsets);
  if(!lasts){ c->err=1; return; }
  int any=0;
  for(int h=0;h<c->nsets;h++){
    const long long *D=c->dset[h]; const Py_ssize_t nD=c->dlen[h];
    int extra=0;
    for(Py_ssize_t j=0;j<nD;j++) if(!c->dead[D[j]]){ c->dead[D[j]]=CC_WINDOW; extra++; }
    const int nd=ndead+extra, rem=c->K-nd;
    int at=-1;
    if(rem>=0 && rem<c->M-nd){
      /* the rem-th smallest last-tier value among draws not yet dismissed */
      int seen=0;
      for(int j=0;j<c->nlast;j++){
        if(c->dead[c->lasto[j]]) continue;
        if(seen==rem){ at=j; break; }
        seen++;
      }
    }
    for(Py_ssize_t j=0;j<nD;j++) if(c->dead[D[j]]==CC_WINDOW) c->dead[D[j]]=0;
    PyObject *v;
    if(at<0){ v=Py_None; Py_INCREF(v); }
    else {
      const float g=c->lastv[at];
      const double r=(double)cc_filter(c,c->k-1,g,alive,nalive,NULL)/(double)c->Nn;
      v=Py_BuildValue("(dd)",(double)g,r);
      if(!v){ Py_DECREF(lasts); c->err=1; return; }
      any=1;
    }
    PyTuple_SET_ITEM(lasts,h,v);
  }
  if(!any){ Py_DECREF(lasts); return; }
  PyObject *th=PyTuple_New(c->k-1), *re=PyTuple_New(c->k), *entry=NULL;
  if(!th||!re){ Py_XDECREF(th); Py_XDECREF(re); Py_DECREF(lasts); c->err=1; return; }
  for(int i=0;i<c->k-1;i++) PyTuple_SET_ITEM(th,i,PyFloat_FromDouble(prefix[i]));
  PyTuple_SET_ITEM(re,0,PyFloat_FromDouble(1.0));
  for(int i=0;i<c->k-1;i++) PyTuple_SET_ITEM(re,i+1,PyFloat_FromDouble(fracs[i]));
  entry=PyTuple_Pack(3,th,re,lasts); Py_DECREF(th); Py_DECREF(re); Py_DECREF(lasts);
  if(!entry || PyList_Append(c->out,entry)) c->err=1;
  Py_XDECREF(entry);
}

static void cc_rec(cc_state *c, int i, double *prefix, double remaining, int ndead,
                   const int *alive, int nalive, double *fracs){
  if(c->err) return;
  if(i==c->k-1){ cc_consider(c,prefix,ndead,alive,nalive,fracs); return; }
  if(i>2){ c->err=1; return; }                   /* k <= 4: levels 0..2 hold a split */
  const long long *low=c->low[i]; const float *lowv=c->lowv[i];
  for(int a=0;a<c->nsplit && !c->err;a++){
    const double share=c->splits[a]*remaining;
    const long long idx=(long long)floor(share*(double)c->K);
    if(idx<1) continue;
    const float g=lowv[idx];
    int cut=0;                                   /* searchsorted(lowv, g, left) */
    { int lo=0, hi=c->K+1; while(lo<hi){ int m=(lo+hi)/2; if(lowv[m]<g) lo=m+1; else hi=m; } cut=lo; }
    /* this level's dismissals carry its own mark, so undoing them leaves the levels above */
    const unsigned char mark=(unsigned char)(i+1);
    int nnew=0;
    for(int j=0;j<cut;j++) if(!c->dead[low[j]]){ c->dead[low[j]]=mark; nnew++; }
    const int cnt=cc_filter(c,i,g,alive,nalive,c->alive[i+1]);
    prefix[i]=(double)g; fracs[i]=(double)cnt/(double)c->Nn;
    if(!(c->prune && fracs[i]>c->useless))
      cc_rec(c,i+1,prefix,remaining-share,ndead+nnew,c->alive[i+1],cnt,fracs);
    for(int j=0;j<cut;j++) if(c->dead[low[j]]==mark) c->dead[low[j]]=0;
  }
}

static PyObject *M_chain_candidates(PyObject *self,PyObject *args){
  (void)self;
  PyObject *So,*Nco,*lowo,*lowvo,*lao,*lvo,*spo,*dso; int K,prune; long long Nn; double useless;
  if(!PyArg_ParseTuple(args,"OOOOOOOiLpdO",&So,&Nco,&lowo,&lowvo,&lao,&lvo,&spo,&K,&Nn,&prune,&useless,&dso)) return NULL;
  if(!PyTuple_Check(dso) || PyTuple_GET_SIZE(dso)<1 || PyTuple_GET_SIZE(dso)>1024){
    PyErr_SetString(PyExc_TypeError,"chain_candidates: dsets a tuple of 1 to 1024 int64 index arrays");
    return NULL;
  }
  const int nsets=(int)PyTuple_GET_SIZE(dso);
  Py_buffer S,N,la,lv,lb[3],lvb[3]; int nlb=0, nds=0;
  Py_buffer *db=(Py_buffer*)calloc((size_t)nsets,sizeof(Py_buffer));
  const long long **dptr=(const long long**)calloc((size_t)nsets,sizeof(*dptr));
  Py_ssize_t *dlen=(Py_ssize_t*)calloc((size_t)nsets,sizeof(Py_ssize_t));
  if(!db || !dptr || !dlen){ free(db); free(dptr); free(dlen); return PyErr_NoMemory(); }
  #define CC_FREE_SETS() do{ for(int q=0;q<nds;q++) PyBuffer_Release(&db[q]); free(db); free(dptr); free(dlen); }while(0)
  if(PyObject_GetBuffer(So,&S,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ CC_FREE_SETS(); return NULL; }
  if(PyObject_GetBuffer(Nco,&N,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); CC_FREE_SETS(); return NULL; }
  if(PyObject_GetBuffer(lao,&la,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); PyBuffer_Release(&N); CC_FREE_SETS(); return NULL; }
  if(PyObject_GetBuffer(lvo,&lv,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); PyBuffer_Release(&N); PyBuffer_Release(&la); CC_FREE_SETS(); return NULL; }
  cc_state c; memset(&c,0,sizeof c);
  int ok = S.ndim==2 && S.itemsize==4 && !strcmp(S.format,"f") && N.ndim==2 && N.itemsize==4 && !strcmp(N.format,"f")
           && la.itemsize==8 && (!strcmp(la.format,"q")||!strcmp(la.format,"l")) && lv.itemsize==4 && !strcmp(lv.format,"f")
           && la.len/8==lv.len/4 && PyTuple_Check(lowo) && PyTuple_Check(lowvo) && PyTuple_Check(spo) && Nn>0 && K>=0;
  if(ok){
    c.M=(int)S.shape[0]; c.k=(int)S.shape[1]; c.R=(int)N.shape[1];
    ok = c.k>=1 && c.k<=4 && N.shape[0]==c.k && PyTuple_GET_SIZE(lowo)==c.k-1 && PyTuple_GET_SIZE(lowvo)==c.k-1 && c.k-1<=3;
  }
  for(int i=0;ok && i<c.k-1;i++){
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(lowo,i),&lb[i],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ ok=0; break; }
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(lowvo,i),&lvb[i],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&lb[i]); ok=0; break; }
    nlb=i+1;
    ok = lb[i].itemsize==8 && lvb[i].itemsize==4 && !strcmp(lvb[i].format,"f") && lb[i].len/8==K+1 && lvb[i].len/4==K+1;
    if(ok){ c.low[i]=(const long long*)lb[i].buf; c.lowv[i]=(const float*)lvb[i].buf;
      for(int j=0;j<=K;j++) if(c.low[i][j]<0 || c.low[i][j]>=c.M){ ok=0; break; } }
  }
  double splits[64]; int nsplit=ok ? (int)PyTuple_GET_SIZE(spo) : 0;
  if(nsplit>64) ok=0;
  for(int a=0;ok && a<nsplit;a++){ splits[a]=PyFloat_AsDouble(PyTuple_GET_ITEM(spo,a)); if(PyErr_Occurred()) ok=0; }
  if(ok){
    c.lasto=(const long long*)la.buf; c.lastv=(const float*)lv.buf; c.nlast=(int)(la.len/8);
    for(int j=0;j<c.nlast;j++) if(c.lasto[j]<0 || c.lasto[j]>=c.M){ ok=0; break; }
  }
  for(int q=0;ok && q<nsets;q++){
    if(PyObject_GetBuffer(PyTuple_GET_ITEM(dso,q),&db[q],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ ok=0; break; }
    nds=q+1;
    ok = db[q].itemsize==8 && (!strcmp(db[q].format,"q")||!strcmp(db[q].format,"l"));
    if(ok){ dptr[q]=(const long long*)db[q].buf; dlen[q]=db[q].len/8;
      for(Py_ssize_t j=0;j<dlen[q];j++) if(dptr[q][j]<0 || dptr[q][j]>=c.M){ ok=0; break; } }
  }
  PyObject *out=NULL;
  if(ok){
    c.K=K; c.Nn=Nn; c.prune=prune; c.useless=useless; c.S=(const float*)S.buf; c.Nc=(const float*)N.buf;
    c.splits=splits; c.nsplit=nsplit; c.nsets=nsets; c.dset=dptr; c.dlen=dlen;
    c.dead=(unsigned char*)calloc((size_t)c.M,1);
    /* level i filters into alive[i+1], i <= k-2: lists 1..k-1 (k <= 4, so at most alive[3]) */
    for(int i=1;i<c.k;i++) c.alive[i]=(int*)malloc(((size_t)c.R+1)*sizeof(int));
    out=PyList_New(0); c.out=out;
    int mem = c.dead && out; for(int i=1;i<c.k;i++) mem = mem && c.alive[i];
    if(mem){
      double prefix[4], fracs[4];
      cc_rec(&c,0,prefix,1.0,0,NULL,0,fracs);
    } else c.err=1;
    free(c.dead); for(int i=1;i<c.k;i++) free(c.alive[i]);
    if(c.err){ Py_XDECREF(out); out=NULL; if(!PyErr_Occurred()) PyErr_NoMemory(); }
  }
  for(int i=0;i<nlb;i++){ PyBuffer_Release(&lb[i]); PyBuffer_Release(&lvb[i]); }
  PyBuffer_Release(&S); PyBuffer_Release(&N); PyBuffer_Release(&la); PyBuffer_Release(&lv);
  CC_FREE_SETS();
  #undef CC_FREE_SETS
  if(!ok && !PyErr_Occurred())
    PyErr_SetString(PyExc_TypeError,"chain_candidates: S float32 (M, k <= 4), Nc float32 (k, R), per earlier tier int64 indices and float32 values of K + 1, the last tier's, splits a tuple of floats, Nn > 0, dsets a tuple of int64 index arrays into S");
  return out;
}
static PyObject *M_l1d_bytes(PyObject *self,PyObject *args){
  (void)self; (void)args;
  return PyLong_FromSize_t(ap_l1d_bytes());
}
static PyObject *M_l2_bytes(PyObject *self,PyObject *args){
  (void)self; (void)args;
  return PyLong_FromSize_t(ap_l2_bytes());
}
static PyObject *M_backend(PyObject *self,PyObject *args){
  (void)self;(void)args;
  return PyUnicode_FromString(ap_isa());
}
static PyObject *M_targets(PyObject *self,PyObject *args){
  (void)self;(void)args;
  int n=ap_target_count();
  PyObject *t=PyTuple_New(n);
  if(!t) return NULL;
  for(int i=0;i<n;i++){
    PyObject *s=PyUnicode_FromString(ap_target_name(i));
    if(!s){ Py_DECREF(t); return NULL; }
    PyTuple_SET_ITEM(t,i,s);
  }
  return t;
}
static PyObject *M_set_target(PyObject *self,PyObject *args){
  (void)self;
  const char *name=NULL;
  if(!PyArg_ParseTuple(args,"z",&name)) return NULL;
  if(ap_set_target(name)){
    PyErr_Format(PyExc_ValueError,"cannot select target %s: it is not a target this build "
                 "holds and this CPU runs, or it is outside MF_ISA's restriction",name);
    return NULL;
  }
  Py_RETURN_NONE;
}
static PyObject *M_pack_peaks(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer bpk,bidx,bval;
  if(!PyArg_ParseTuple(args,"w*y*y*",&bpk,&bidx,&bval)) return NULL;
  Py_ssize_t count=bpk.len/(Py_ssize_t)sizeof(ap_structured_peak);
  if(count==0){
    PyBuffer_Release(&bpk);PyBuffer_Release(&bidx);PyBuffer_Release(&bval);
    Py_RETURN_NONE;
  }
  if(bpk.len!=count*(Py_ssize_t)sizeof(ap_structured_peak) || bval.len<count*8){
    PyBuffer_Release(&bpk);PyBuffer_Release(&bidx);PyBuffer_Release(&bval);
    PyErr_SetString(PyExc_ValueError,"mismatched buffer sizes in pack_peaks");
    return NULL;
  }
  ap_structured_peak * restrict dst=(ap_structured_peak*)bpk.buf;
  const float * restrict vl=(const float*)bval.buf;
  if(bidx.len>=count*4 && bidx.len<count*8){
    const int32_t * restrict ix32=(const int32_t*)bidx.buf;
    for(Py_ssize_t i=0;i<count;i++){
      dst[i].index=(int64_t)ix32[i];
      dst[i].re=vl[2*i];
      dst[i].im=vl[2*i+1];
    }
  } else if(bidx.len>=count*8){
    const int64_t * restrict ix64=(const int64_t*)bidx.buf;
    for(Py_ssize_t i=0;i<count;i++){
      dst[i].index=ix64[i];
      dst[i].re=vl[2*i];
      dst[i].im=vl[2*i+1];
    }
  } else {
    PyBuffer_Release(&bpk);PyBuffer_Release(&bidx);PyBuffer_Release(&bval);
    PyErr_SetString(PyExc_ValueError,"idx buffer too small in pack_peaks");
    return NULL;
  }
  PyBuffer_Release(&bpk);PyBuffer_Release(&bidx);PyBuffer_Release(&bval);
  Py_RETURN_NONE;
}
/* window_bin_keep(win_starts, binsize, t, s, v, keep, is_float) -> kept count, or -1.
   Peaks ordered by template, then sample: the partial bins of one window bin (a block edge
   inside it) are adjacent runs. keep receives, in order, the index of each run's first
   peak at the run's largest |v|; the count is len(t) when nothing merged. -1: not in that
   order (the caller sorts). win_starts: the ascending window starts, every peak at or after
   the first. s is int64, or float64 when is_float (interpolated samples); a float sample's
   bin is numpy's floor division, so the result matches the array form. */
static inline int64_t wbk_bin_f(double a, double b){
  /* numpy's float floor_divide (npy_divmod), for a >= 0, b > 0 */
  const double mod=fmod(a,b), div=(a-mod)/b;
  double q=floor(div);
  if(div-q>0.5) q+=1.0;
  return (int64_t)q;
}
static PyObject *M_window_bin_keep(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer bw,bt,bs,bv,bk; long long binsize; int isf;
  if(!PyArg_ParseTuple(args,"y*Ly*y*y*w*p",&bw,&binsize,&bt,&bs,&bv,&bk,&isf)) return NULL;
  const Py_ssize_t n=bt.len/8, nw=bw.len/8;
  long long r=-2;
  if(binsize>0 && nw>0 && bt.len==n*8 && bs.len==n*8 && bv.len==n*8 && bk.len>=n*8){
    const int64_t *W=(const int64_t*)bw.buf, *t=(const int64_t*)bt.buf;
    const int64_t *si=(const int64_t*)bs.buf; const double *sf=(const double*)bs.buf;
    const float *v=(const float*)bv.buf; int64_t *keep=(int64_t*)bk.buf;
    Py_ssize_t w=0, kept=0, best=-1; float bestm=0.f;
    int64_t kt=0, kw=0, kb=0;
    r=0;
    for(Py_ssize_t i=0;i<n;i++){
      const double x = isf ? sf[i] : (double)si[i];
      if(i>0 && (t[i]<t[i-1] || (t[i]==t[i-1] && (isf ? sf[i]<=sf[i-1] : si[i]<=si[i-1])))){ r=-1; break; }
      if(i==0 || t[i]!=t[i-1]) w=0;
      while(w+1<nw && (isf ? (double)W[w+1]<=x : W[w+1]<=si[i])) w++;
      if(isf ? !(x>=(double)W[w]) : si[i]<W[w]){ r=-2; break; }
      const int64_t b = isf ? wbk_bin_f(x-(double)W[w],(double)binsize) : (si[i]-W[w])/binsize;
      const float m=hypotf(v[2*i],v[2*i+1]);
      if(i>0 && t[i]==kt && (int64_t)w==kw && b==kb){
        if(m>bestm){ bestm=m; best=i; }
        continue;
      }
      if(best>=0) keep[kept++]=best;
      kt=t[i]; kw=w; kb=b; best=i; bestm=m;
    }
    if(r==0){ if(best>=0) keep[kept++]=best; r=kept; }
  }
  PyBuffer_Release(&bw);PyBuffer_Release(&bt);PyBuffer_Release(&bs);
  PyBuffer_Release(&bv);PyBuffer_Release(&bk);
  if(r==-2){ PyErr_SetString(PyExc_ValueError,"window_bin_keep: mismatched buffers, binsize < 1 "
                             "or a peak before the first window"); return NULL; }
  return PyLong_FromLongLong(r);
}
/* taps_to_spectra's transforms, kept per block length: a consumer's get_filter_f makes one
   spectrum a call (pycbc's power chisq, about 14,000 calls in the 171,828-template job), and
   creating the plan and its buffer was 6 of its 7.7 us (Zen 5, n = 1024). Taken and given back
   under the GIL, which the call holds on both sides of its transforms, so two threads never
   share one; a busy or missing slot gives a plan made for the call, as before. Keyed by the
   ISA as well, which set_target can change. */
#define T2S_SLOTS 8
static struct { size_t n; const char *isa; ap_plan *plan; float *buf; int busy; } t2s_tab[T2S_SLOTS];
static long long t2s_made = 0;     /* plans taps_to_spectra has made, kept or not */

static PyObject *M_t2s_plans(PyObject *self, PyObject *args){
  (void)self; (void)args;
  return PyLong_FromLongLong(t2s_made);
}

static int t2s_take(size_t n){
  const char *isa = ap_isa();
  int spare = -1;
  for(int i = 0; i < T2S_SLOTS; i++){
    if(t2s_tab[i].busy) continue;
    if(t2s_tab[i].plan && t2s_tab[i].n == n && t2s_tab[i].isa == isa){ t2s_tab[i].busy = 1; return i; }
    if(spare < 0 || (t2s_tab[spare].plan && !t2s_tab[i].plan)) spare = i;
  }
  if(spare < 0) return -1;
  if(t2s_tab[spare].plan){ ap_destroy(t2s_tab[spare].plan); free(t2s_tab[spare].buf); }
  t2s_tab[spare].plan = ap_create(n);
  t2s_made++;
  t2s_tab[spare].buf = t2s_tab[spare].plan ? (float*)ap_alloc64(2 * n * sizeof(float)) : NULL;
  if(!t2s_tab[spare].plan || !t2s_tab[spare].buf){
    if(t2s_tab[spare].plan) ap_destroy(t2s_tab[spare].plan);
    free(t2s_tab[spare].buf);
    t2s_tab[spare].plan = NULL; t2s_tab[spare].buf = NULL;
    return -1;
  }
  t2s_tab[spare].n = n; t2s_tab[spare].isa = isa; t2s_tab[spare].busy = 1;
  return spare;
}

static PyObject *M_taps_to_spectra(PyObject *self, PyObject *args){
  Py_buffer btaps, bcnt, bout;
  Py_ssize_t n, max_taps;
  int cplx = 0;     /* complex64 (quadrature) taps instead of float32 */
  if(!PyArg_ParseTuple(args, "y*y*nnw*|p", &btaps, &bcnt, &n, &max_taps, &bout, &cplx)) return NULL;

  if(n <= 0 || max_taps <= 0){
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_ValueError, "n and max_taps must be positive");
    return NULL;
  }

  size_t n_elem_taps = (size_t)(btaps.len / ((cplx ? 2 : 1) * sizeof(float)));
  if(n_elem_taps % (size_t)max_taps != 0){
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_ValueError, "invalid taps shape");
    return NULL;
  }
  size_t T = n_elem_taps / (size_t)max_taps;
  if(!buf_holds(bout.len,(Py_ssize_t)T,n,(Py_ssize_t)(2*sizeof(float)))){
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_ValueError, "output buffer too small");
    return NULL;
  }

  int is_64;
  if(bcnt.len == (Py_ssize_t)(T * sizeof(int64_t))){
    is_64 = 1;
  } else if(bcnt.len == (Py_ssize_t)(T * sizeof(int32_t))){
    is_64 = 0;
  } else {
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_ValueError, "counts buffer size mismatch: expected T int64 or T int32 elements");
    return NULL;
  }

  const int slot = t2s_take((size_t)n);
  ap_plan *plan = slot >= 0 ? t2s_tab[slot].plan : (t2s_made++, ap_create((size_t)n));
  if(!plan){
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_RuntimeError, "failed to create FFT plan");
    return NULL;
  }

  float *in_buf = slot >= 0 ? t2s_tab[slot].buf : (float*)ap_alloc64(2 * (size_t)n * sizeof(float));
  if(!in_buf){
    ap_destroy(plan);
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_NoMemory();
    return NULL;
  }
  memset(in_buf, 0, 2 * (size_t)n * sizeof(float));

  const float *taps = (const float*)btaps.buf;
  float *out = (float*)bout.buf;
  const int64_t *cnt64 = is_64 ? (const int64_t*)bcnt.buf : NULL;
  const int32_t *cnt32 = is_64 ? NULL : (const int32_t*)bcnt.buf;

  Py_BEGIN_ALLOW_THREADS
  for(size_t t = 0; t < T; t++){
    int64_t raw_cnt = is_64 ? cnt64[t] : (int64_t)cnt32[t];
    if(raw_cnt <= 0){
      memset(out + t * 2 * (size_t)n, 0, 2 * (size_t)n * sizeof(float));
      continue;
    }
    size_t count = (size_t)raw_cnt;
    if(count > (size_t)max_taps) count = (size_t)max_taps;
    if(count > (size_t)n) count = (size_t)n;
    size_t half = count / 2;
    size_t pos_len = count - half;
    if(cplx){
      const float *row = taps + t * 2 * (size_t)max_taps;
      memcpy(in_buf, row + 2 * half, 2 * pos_len * sizeof(float));
      if(half) memcpy(in_buf + 2 * ((size_t)n - half), row, 2 * half * sizeof(float));
    } else {
      const float *row = taps + t * (size_t)max_taps;
      for(size_t i = 0; i < pos_len; i++) in_buf[2 * i] = row[half + i];
      for(size_t i = 0; i < half; i++) in_buf[2 * ((size_t)n - half + i)] = row[i];
    }
    ap_fft(plan, in_buf, out + t * 2 * (size_t)n, AP_FORWARD);
    /* Clear only the active support written above so in_buf stays zeroed without 2n memsets. */
    memset(in_buf, 0, 2 * pos_len * sizeof(float));
    if(half) memset(in_buf + 2 * ((size_t)n - half), 0, 2 * half * sizeof(float));
  }
  Py_END_ALLOW_THREADS

  if(slot >= 0){
    t2s_tab[slot].busy = 0;
  } else {
    free(in_buf);
    ap_destroy(plan);
  }
  PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
  Py_RETURN_NONE;
}

int ap_gate16_available(void);
static PyObject *M_gate16(PyObject *self, PyObject *noargs){
  (void)self; (void)noargs;
  return PyBool_FromLong(ap_gate16_available());
}




/* gate16_max(N, data, templates, nt) -> float32 array of nt: the FP16 first gate's
   statistic, each pair's FP16 maximum (ap_gate16_run, one data row, window [0, N)), or None where there is no
   FP16 gate. Measurement only (tools/gate_margin.py --gate cpu-g16). data: N complex64,
   templates: nt x N complex64, correlated as the tier does (templates conjugated at ingest). */
void *ap_gate16_create(size_t m, int nd, int nt);
void ap_gate16_destroy(void *g);
int ap_gate16_set_template(void *g, int t, const float *spec);
int ap_gate16_set_data(void *g, int d, const float *spec);
int ap_gate16_run(void *g, int d0, int nd, int t0, int nt, size_t ws, size_t we, ap_peak *out);
static PyObject *M_gate16_max(PyObject *self, PyObject *args){
  (void)self; Py_ssize_t N; Py_buffer bd, bt; int nt;
  if(!PyArg_ParseTuple(args,"ny*y*i",&N,&bd,&bt,&nt)) return NULL;
  PyObject *res=NULL;
  void *g=ap_gate16_create((size_t)N,1,nt);
  if(!g){ PyBuffer_Release(&bd); PyBuffer_Release(&bt); Py_RETURN_NONE; }
  ap_peak *pk=calloc((size_t)nt,sizeof(ap_peak));
  int ok = pk && N>0 && nt>0 && buf_holds(bd.len,N,1,8) && buf_holds(bt.len,N,nt,8);
  if(ok){
    for(int t=0;t<nt&&ok;t++) ok = ap_gate16_set_template(g,t,(const float*)bt.buf+(size_t)t*2*N)==0;
    ok = ok && ap_gate16_set_data(g,0,(const float*)bd.buf)==0;
    ok = ok && ap_gate16_run(g,0,1,0,nt,0,(size_t)N,pk)==0;
  }
  if(ok){
    PyObject *b=PyBytes_FromStringAndSize(NULL,(Py_ssize_t)nt*sizeof(float));
    if(b){ float *f=(float*)PyBytes_AS_STRING(b);
      for(int t=0;t<nt;t++) f[t]= pk[t].index>=0 ? pk[t].magnitude : -1.0f;
      res=b; }
  } else { PyErr_SetString(PyExc_ValueError,"gate16_max failed"); }
  free(pk); ap_gate16_destroy(g); PyBuffer_Release(&bd); PyBuffer_Release(&bt);
  return res;
}


static PyObject *M_price_direct(PyObject *self,PyObject *args){
  (void)self; int x_real=0, tap_cplx=0;
  if(!PyArg_ParseTuple(args,"|pp",&x_real,&tap_cplx)) return NULL;
  return PyFloat_FromDouble(ap_hmf_price_direct_mode(x_real,tap_cplx));
}

/* Root(n): the root stage of a hierarchical search (ap_root_real). */
typedef struct { PyObject_HEAD ap_root *r; int busy; /* GUARDED */ } RootObject;

static PyObject *Root_new(PyTypeObject *type, PyObject *args, PyObject *kw){
  (void)kw; Py_ssize_t n;
  if(!PyArg_ParseTuple(args,"n",&n)) return NULL;
  if(n<128 || (n&(n-1))){
    PyErr_SetString(PyExc_ValueError,"n must be a power of two of at least 128"); return NULL;
  }
  RootObject *self=(RootObject*)type->tp_alloc(type,0);
  if(!self) return NULL;
  self->r=ap_root_create((size_t)n);
  if(!self->r){
    Py_DECREF(self);
    PyErr_SetString(PyExc_ValueError,"unsupported root length"); return NULL;
  }
  return (PyObject*)self;
}
static void Root_dealloc(RootObject *self){
  ap_root_destroy(self->r);
  Py_TYPE(self)->tp_free((PyObject*)self);
}
/* real(D, T, k0, k1, scale, out): D, T complex64 one-sided spectra of at least n/2 + 1 bins,
   out float32 of n samples (C-contiguous, writable). */
static PyObject *Root_real(RootObject *self, PyObject *args){
  Py_buffer bd, bt, bo; Py_ssize_t k0, k1; float scale;
  if(!PyArg_ParseTuple(args,"y*y*nnfw*",&bd,&bt,&k0,&k1,&scale,&bo)) return NULL;
  const size_t n=ap_root_length(self->r), nbins=(size_t)(bd.len/8);
  int rc=-1;
  if(bd.len%8==0 && bt.len>=bd.len && bo.len>=(Py_ssize_t)(n*sizeof(float))
     && k0>=0 && k1>=k0){
    Py_BEGIN_ALLOW_THREADS
    rc=ap_root_real(self->r,(const float*)bd.buf,(const float*)bt.buf,nbins,
                    (size_t)k0,(size_t)k1,scale,(float*)bo.buf);
    Py_END_ALLOW_THREADS
  }
  PyBuffer_Release(&bd); PyBuffer_Release(&bt); PyBuffer_Release(&bo);
  if(rc){
    PyErr_SetString(PyExc_ValueError,"root: spectra shorter than n/2 + 1 bins, band outside "
                    "[0, n/2 + 1), or output shorter than n samples"); return NULL;
  }
  Py_RETURN_NONE;
}
static PyObject *Root_length(RootObject *self, PyObject *unused){
  (void)unused; return PyLong_FromSize_t(ap_root_length(self->r));
}
GUARDED(RootObject,Root_real)
GUARDED(RootObject,Root_length)
static PyMethodDef Root_methods[]={
  {"real",(PyCFunction)Root_real_g,METH_VARARGS,
   "real(D, T, k0, k1, scale, out): out = scale * C2R(conj(T) D over bins [k0, k1))"},
  {"length",(PyCFunction)Root_length_g,METH_NOARGS,"length() -> n"},
  {NULL,NULL,0,NULL}};
static PyTypeObject RootType={
  PyVarObject_HEAD_INIT(NULL,0)
  .tp_name="matchedfilter._core.Root",
  .tp_basicsize=sizeof(RootObject),
  .tp_flags=Py_TPFLAGS_DEFAULT,
  .tp_new=Root_new,
  .tp_dealloc=(destructor)Root_dealloc,
  .tp_methods=Root_methods,
  .tp_doc="Root(n): the root stage of a hierarchical search, to a real series of n samples",
};

/* plan_best: the cheapest of a chain's candidate plans (gatechain.plan_chain), priced as its
   Python loop prices them on a CostModel, operation for operation. */
/* The Python loop rounds every product and sum; a compiler that fuses a product into the
   sum that follows (aarch64 by default) gave costs one place off, and on a tie another
   plan. These functions are compiled with contraction off, whatever the file's flags. */
#if defined(__clang__)
#define PB_EXACT
#define PB_EXACT_BODY _Pragma("clang fp contract(off)")
#elif defined(__GNUC__)
#define PB_EXACT __attribute__((optimize("fp-contract=off")))
#define PB_EXACT_BODY
#else
#define PB_EXACT
#define PB_EXACT_BODY _Pragma("fp_contract(off)")
#endif
enum { PB_ROWS=64, PB_TIERS=8 };
typedef struct { int n; double fs[PB_ROWS], vs[PB_ROWS]; } pb_table;

/* A (log densities, values) pair of equal-length tuples of floats into t. 0 on success. */
static int pb_read(PyObject *pair, pb_table *t){
  if(!PyTuple_Check(pair) || PyTuple_GET_SIZE(pair)!=2) return -1;
  PyObject *fs=PyTuple_GET_ITEM(pair,0), *vs=PyTuple_GET_ITEM(pair,1);
  if(!PyTuple_Check(fs) || !PyTuple_Check(vs)) return -1;
  const Py_ssize_t n=PyTuple_GET_SIZE(fs);
  if(n<1 || n>PB_ROWS || PyTuple_GET_SIZE(vs)!=n) return -1;
  for(Py_ssize_t i=0;i<n;i++){
    t->fs[i]=PyFloat_AsDouble(PyTuple_GET_ITEM(fs,i));
    t->vs[i]=PyFloat_AsDouble(PyTuple_GET_ITEM(vs,i));
  }
  t->n=(int)n;
  return PyErr_Occurred() ? -1 : 0;
}

/* gatechain._interp_clamped */
PB_EXACT static double pb_interp(double x, const pb_table *t){
  PB_EXACT_BODY
  const double *fs=t->fs, *vs=t->vs;
  if(x<=fs[0]) return vs[0];
  if(x>=fs[t->n-1]) return vs[t->n-1];
  int j=0;
  const int last=t->n-2;
  while(j<last && fs[j+1]<=x) j++;
  const double dx=fs[j+1]-fs[j];
  if(dx==0.0) return vs[j+1];
  const double dy=vs[j+1]-vs[j];
  if(dy==0.0) return vs[j];
  return (x-fs[j])*(dy/dx)+vs[j];
}
/* CostModel._interp: a table's value at density f */
PB_EXACT static double pb_cost(const pb_table *t, double f){
  PB_EXACT_BODY
  return pb_interp(log(f>1e-12 ? f : 1e-12), t);
}

/* plan_best(cands, hws, first, later, refine, direct[, feed]) -> (cost, candidate, last) or None
   cands: the list gatechain._chain_candidates returns, (earlier thresholds, earlier reach,
   lasts) each, lasts a (threshold, reach) or None per half-width. hws: the half-widths, an
   int or None each. first: (cost per pair of the dense first tier, None) or (that, (the
   screen's cost per pair, its cost per pair passed, the screen's excess table, tie)).
   later: per later tier (its sparse table, its sparse table behind a screen). refine: the
   refine table. direct: None, or (base, per lag, lags per half-width step, fraction, None or
   (share, the last tier's sparse table)). A table is (log densities, values), tuples of
   floats. feed: None, or a GPU's feed (CostModel.feed_delta, as gatechain._costmodel.feed_rule
   gives it): (mode, band, full, threshold), added to each candidate's cost -- mode 0 full,
   1 band, 2 band where the refine fraction (0 where the direct refine prices the pair) is
   below threshold, else full. Returns the cheapest plan's cost and where it is (the first of
   equal costs), or None when no candidate has a last tier. */
PB_EXACT static PyObject *M_plan_best(PyObject *self,PyObject *args){
  PB_EXACT_BODY
  (void)self;
  PyObject *cands,*hws,*first,*later,*refine,*direct,*feed=Py_None;
  if(!PyArg_ParseTuple(args,"O!O!O!O!OO|O",&PyList_Type,&cands,&PyTuple_Type,&hws,
                       &PyTuple_Type,&first,&PyTuple_Type,&later,&refine,&direct,&feed)) return NULL;
  pb_table t_refine, t_excess, t_last, t_plain[PB_TIERS], t_screened[PB_TIERS];
  const Py_ssize_t nl=PyTuple_GET_SIZE(later), nh=PyTuple_GET_SIZE(hws);
  int ok = nl>=1 && nl<=PB_TIERS && nh<=PB_ROWS && PyTuple_GET_SIZE(first)==2
           && pb_read(refine,&t_refine)==0;
  for(Py_ssize_t i=0;ok && i<nl;i++){
    PyObject *pair=PyTuple_GET_ITEM(later,i);
    ok = PyTuple_Check(pair) && PyTuple_GET_SIZE(pair)==2
         && pb_read(PyTuple_GET_ITEM(pair,0),&t_plain[i])==0
         && pb_read(PyTuple_GET_ITEM(pair,1),&t_screened[i])==0;
  }
  double dense=0.0, sc_dense=0.0, sc_recheck=0.0, tie=0.0;
  int has_screen=0;
  if(ok){
    dense=PyFloat_AsDouble(PyTuple_GET_ITEM(first,0));
    PyObject *sc=PyTuple_GET_ITEM(first,1);
    if(sc!=Py_None){
      ok = PyTuple_Check(sc) && PyTuple_GET_SIZE(sc)==4 && pb_read(PyTuple_GET_ITEM(sc,2),&t_excess)==0;
      if(ok){
        has_screen=1;
        sc_dense=PyFloat_AsDouble(PyTuple_GET_ITEM(sc,0));
        sc_recheck=PyFloat_AsDouble(PyTuple_GET_ITEM(sc,1));
        tie=PyFloat_AsDouble(PyTuple_GET_ITEM(sc,3));
      }
    }
  }
  int prices_dir=0, has_last=0;
  double dbase=0.0, dlag=0.0, dfrac=1.0, dmfrac=0.0;
  long long R=0;
  if(ok && direct!=Py_None){
    ok = PyTuple_Check(direct) && PyTuple_GET_SIZE(direct)==5;
    if(ok){
      prices_dir=1;
      dbase=PyFloat_AsDouble(PyTuple_GET_ITEM(direct,0));
      dlag=PyFloat_AsDouble(PyTuple_GET_ITEM(direct,1));
      R=PyLong_AsLongLong(PyTuple_GET_ITEM(direct,2));
      dfrac=PyFloat_AsDouble(PyTuple_GET_ITEM(direct,3));
      PyObject *ls=PyTuple_GET_ITEM(direct,4);
      if(ls!=Py_None){
        ok = PyTuple_Check(ls) && PyTuple_GET_SIZE(ls)==2 && pb_read(PyTuple_GET_ITEM(ls,1),&t_last)==0;
        if(ok){ has_last=1; dmfrac=PyFloat_AsDouble(PyTuple_GET_ITEM(ls,0)); }
      }
    }
  }
  int feed_mode=-1;
  double feed_band=0.0, feed_full=0.0, feed_thr=0.0;
  if(ok && feed!=Py_None){
    ok = PyTuple_Check(feed) && PyTuple_GET_SIZE(feed)==4;
    if(ok){
      feed_mode=(int)PyLong_AsLong(PyTuple_GET_ITEM(feed,0));
      feed_band=PyFloat_AsDouble(PyTuple_GET_ITEM(feed,1));
      feed_full=PyFloat_AsDouble(PyTuple_GET_ITEM(feed,2));
      feed_thr=PyFloat_AsDouble(PyTuple_GET_ITEM(feed,3));
      ok = feed_mode>=0 && feed_mode<=2;
    }
  }
  /* a half-width's direct price does not depend on the candidate */
  int hw_set[PB_ROWS];
  double hw_price[PB_ROWS];
  for(Py_ssize_t h=0;ok && h<nh;h++){
    PyObject *hw=PyTuple_GET_ITEM(hws,h);
    hw_set[h] = hw!=Py_None;
    hw_price[h] = hw_set[h] ? dbase + dlag*(double)(2*PyLong_AsLongLong(hw)*R+1) : 0.0;
  }
  if(!ok || PyErr_Occurred()){
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"plan_best: invalid tables");
    return NULL;
  }
  const Py_ssize_t nc=PyList_GET_SIZE(cands);
  int found=0;
  double best=0.0;
  Py_ssize_t best_c=0, best_h=0;
  for(Py_ssize_t ci=0;ci<nc;ci++){
    PyObject *cand=PyList_GET_ITEM(cands,ci);
    if(!PyTuple_Check(cand) || PyTuple_GET_SIZE(cand)!=3) goto bad;
    PyObject *preach=PyTuple_GET_ITEM(cand,1), *lasts=PyTuple_GET_ITEM(cand,2);
    if(!PyTuple_Check(preach) || PyTuple_GET_SIZE(preach)!=nl+1
       || !PyTuple_Check(lasts)) goto bad;
    /* a last per half-width, as far as both go */
    const Py_ssize_t nlast = PyTuple_GET_SIZE(lasts)<nh ? PyTuple_GET_SIZE(lasts) : nh;
    /* CostModel.first_tier_for: the dense tier, or the screen where it is no dearer */
    const double r1=PyFloat_AsDouble(PyTuple_GET_ITEM(preach,1));
    double c_prefix=dense;
    int screened=0;
    if(has_screen){
      const double x = r1>1e-6 ? r1 : 1e-6;
      const double grown = x*exp(pb_interp(log(x),&t_excess));
      const double passed = grown<1.0 ? grown : 1.0;
      const double cq = sc_dense + passed*sc_recheck;
      if(cq <= dense*(1.0+tie)){ c_prefix=cq; screened=1; }
    }
    for(Py_ssize_t i=0;i<nl;i++){
      const double ri=PyFloat_AsDouble(PyTuple_GET_ITEM(preach,i+1));
      c_prefix += ri*pb_cost(screened ? &t_screened[i] : &t_plain[i], ri);
    }
    for(Py_ssize_t h=0;h<nlast;h++){
      PyObject *last=PyTuple_GET_ITEM(lasts,h);
      if(last==Py_None) continue;
      if(!PyTuple_Check(last) || PyTuple_GET_SIZE(last)!=2) goto bad;
      const double f=PyFloat_AsDouble(PyTuple_GET_ITEM(last,1));
      double r_cost=pb_cost(&t_refine,f);
      if(hw_set[h] && prices_dir){
        double d_cost=hw_price[h];
        if(has_last && f>=0.05) d_cost += dmfrac*pb_cost(&t_last,f);
        d_cost = d_cost<r_cost ? d_cost : r_cost;
        r_cost = (1.0-dfrac)*r_cost + dfrac*d_cost;
      }
      double c=c_prefix+f*r_cost;
      if(feed_mode>=0){
        /* CostModel.feed_delta: the band forward's or the full one's, by the refine fraction */
        const double r = (hw_set[h] && prices_dir) ? 0.0 : (f>1.0 ? 1.0 : (f>0.0 ? f : 0.0));
        c += (feed_mode==1 || (feed_mode==2 && r<feed_thr)) ? feed_band : feed_full;
      }
      if(!found || c<best){ found=1; best=c; best_c=ci; best_h=h; }
    }
  }
  if(PyErr_Occurred()) return NULL;
  if(!found) Py_RETURN_NONE;
  return Py_BuildValue("dnn",best,best_c,best_h);
bad:
  if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"plan_best: invalid candidates");
  return NULL;
}

int ap_tier0_pair_scores(const float *ur, const float *ui, const float *sr, const float *si,
                         const double *v, long long mc, long long len, long long nsh,
                         float floor, float *r2, int32_t *bs);          /* src/tier0.cc */
/* tier0_pair_scores(Ur, Ui, Sr, Si, v_c, floor, out_rho2, out_s): single-core shifted pair
   coherence over an m_c-template chunk without multi-threaded BLAS wakeup overhead
   (src/tier0.cc); a score below floor is only known to be below it. */
static PyObject *M_tier0_pair_scores(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer ur={0},ui={0},sr={0},si={0},vc={0},r2={0},bs={0};
  PyObject *uro,*uio,*sro,*sio,*vco,*r2o,*bso;
  double floor;
  if(!PyArg_ParseTuple(args,"OOOOOdOO",&uro,&uio,&sro,&sio,&vco,&floor,&r2o,&bso)) return NULL;
  Py_buffer *bufs[7]={&ur,&ui,&sr,&si,&vc,&r2,&bs};
  PyObject *objs[7]={uro,uio,sro,sio,vco,r2o,bso};
  int got=0, ok=1;
  for(int i=0;i<7;i++){
    int flags = (i>=5) ? (PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)
                       : (PyBUF_C_CONTIGUOUS|PyBUF_FORMAT);
    if(PyObject_GetBuffer(objs[i],bufs[i],flags)<0){ ok=0; break; }
    got=i+1;
  }
  Py_ssize_t mc=0, len=0, nsh=0;
  if(ok){
    ok = ur.ndim==2 && ui.ndim==2 && sr.ndim==2 && si.ndim==2
         && vc.ndim==1 && r2.ndim==2 && bs.ndim==2
         && ur.itemsize==4 && strcmp(ur.format,"f")==0
         && ui.itemsize==4 && strcmp(ui.format,"f")==0
         && sr.itemsize==4 && strcmp(sr.format,"f")==0
         && si.itemsize==4 && strcmp(si.format,"f")==0
         && vc.itemsize==8 && strcmp(vc.format,"d")==0
         && r2.itemsize==4 && strcmp(r2.format,"f")==0
         && bs.itemsize==4 && (strcmp(bs.format,"i")==0 || strcmp(bs.format,"l")==0);
    if(ok){
      mc=ur.shape[0]; len=ur.shape[1]; nsh=sr.shape[0];
      ok = mc>=0 && len>=1 && nsh>=1
           && ui.shape[0]==mc && ui.shape[1]==len
           && sr.shape[1]==len && si.shape[0]==nsh && si.shape[1]==len
           && vc.shape[0]==mc
           && r2.shape[0]==mc && r2.shape[1]==mc
           && bs.shape[0]==mc && bs.shape[1]==mc;
    }
  }
  if(!ok){
    for(int i=0;i<got;i++) PyBuffer_Release(bufs[i]);
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_pair_scores: invalid buffer shapes or dtypes");
    return NULL;
  }
  const float *Urp=(const float*)ur.buf, *Uip=(const float*)ui.buf;
  const float *Srp=(const float*)sr.buf, *Sip=(const float*)si.buf;
  const double *Vcp=(const double*)vc.buf;
  /* the float floor at or below the double one: every score at or above floor is exact */
  float floorf=(float)floor;
  if((double)floorf>floor) floorf=nextafterf(floorf,-HUGE_VALF);
  int rc;
  Py_BEGIN_ALLOW_THREADS
  rc=ap_tier0_pair_scores(Urp,Uip,Srp,Sip,Vcp,(long long)mc,(long long)len,(long long)nsh,
                          floorf,(float*)r2.buf,(int32_t*)bs.buf);
  Py_END_ALLOW_THREADS
  for(int i=0;i<got;i++) PyBuffer_Release(bufs[i]);
  if(rc) return PyErr_NoMemory();
  Py_RETURN_NONE;
}

void ap_tier0_refine_lags(const double *prod_ab, const double *exp_all, const int64_t *pdl,
                          long long npairs, long long len, long long R, long long half_span,
                          int64_t *out_dl, double *out_g);               /* src/tier0.cc */
static PyObject *M_tier0_refine_lags(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer pab={0}, ex={0}, pdl={0}, odl={0}, og={0};
  PyObject *pabo, *exo, *pdlo, *odlo, *ogo=Py_None;
  long long R=0, half_span=0;
  if(!PyArg_ParseTuple(args,"OOOLLOO",&pabo,&exo,&pdlo,&R,&half_span,&odlo,&ogo)) return NULL;
  int has_og = (ogo != Py_None);
  int ok = 1;
  int g_pab=0, g_ex=0, g_pdl=0, g_odl=0, g_og=0;
  if(PyObject_GetBuffer(pabo,&pab,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else g_pab=1;
  if(ok && PyObject_GetBuffer(exo,&ex,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else if(ok) g_ex=1;
  if(ok && PyObject_GetBuffer(pdlo,&pdl,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else if(ok) g_pdl=1;
  if(ok && PyObject_GetBuffer(odlo,&odl,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else if(ok) g_odl=1;
  if(ok && has_og){
    if(PyObject_GetBuffer(ogo,&og,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0;
    else g_og=1;
  }
  Py_ssize_t npairs=0, len=0;
  if(ok){
    ok = pab.ndim==2 && ex.ndim==2 && pdl.ndim==1 && odl.ndim==1
         && pab.itemsize==16 && strcmp(pab.format,"Zd")==0
         && ex.itemsize==16 && strcmp(ex.format,"Zd")==0
         && pdl.itemsize==8 && (strcmp(pdl.format,"q")==0 || strcmp(pdl.format,"l")==0)
         && odl.itemsize==8 && (strcmp(odl.format,"q")==0 || strcmp(odl.format,"l")==0);
    if(ok && has_og){
      ok = og.ndim==1 && og.itemsize==16 && strcmp(og.format,"Zd")==0;
    }
    if(ok){
      npairs=pab.shape[0]; len=pab.shape[1];
      ok = npairs>=0 && len>=1 && R>=0 && half_span>=0
           && ex.shape[0]==2*(Py_ssize_t)R+1 && ex.shape[1]==len
           && pdl.shape[0]==npairs && odl.shape[0]==npairs
           && (!has_og || og.shape[0]==npairs);
    }
  }
  if(!ok){
    if(g_pab) PyBuffer_Release(&pab);
    if(g_ex) PyBuffer_Release(&ex);
    if(g_pdl) PyBuffer_Release(&pdl);
    if(g_odl) PyBuffer_Release(&odl);
    if(g_og) PyBuffer_Release(&og);
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_refine_lags: invalid buffer shapes or dtypes");
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  ap_tier0_refine_lags((const double*)pab.buf,(const double*)ex.buf,(const int64_t*)pdl.buf,
                       (long long)npairs,(long long)len,R,half_span,
                       (int64_t*)odl.buf, has_og ? (double*)og.buf : NULL);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&pab); PyBuffer_Release(&ex); PyBuffer_Release(&pdl); PyBuffer_Release(&odl);
  if(g_og) PyBuffer_Release(&og);
  Py_RETURN_NONE;
}

long long ap_tier0_match(
    const int64_t *order, long long count, long long nodes, const float *U, const double *v,
    const float *sr, const float *si, const int64_t *shift_lags, long long K, long long nsh,
    double floor, const int32_t *sizes, long long size_cap, long long chunk, int32_t *a,
    int32_t *b, int64_t *dl);                                          /* src/tier0_match.cc */
/* tier0_match(order, U, v, Sr, Si, shift_lags, floor, sizes, size_cap, chunk, a, b, dl) -> count
   The matching of a level's vectors into pairs, chunk by chunk (src/tier0_match.cc).
   order (count) int64, the nodes in the order they are chunked; U (nodes, K) complex64; v
   (nodes) float64; Sr, Si (nsh, K) float32 and shift_lags (nsh) int64, the coarse shifts in
   the order they are tried; sizes (nodes) int32 with size_cap, or None; chunk the nodes a
   chunk holds. Written: a, b (at least count // 2) int32 and dl int64, a pair's smaller
   index, its larger and the lag of the larger against the smaller. Returns the number of
   pairs. */
static PyObject *M_tier0_match(PyObject *self,PyObject *args){
  (void)self;
  enum { iORD,iU,iV,iSR,iSI,iSL,iSZ,oA,oB,oDL, NUSED };
  static const char *fmt[NUSED]={"q","Zf","d","f","f","q","i","i","i","q"};
  static const int ndim[NUSED]={1,2,1,2,2,1,1,1,1,1};
  PyObject *o[NUSED];
  Py_buffer b[NUSED];
  double floor=0.0;
  long long size_cap=0, chunk=0;
  int have[NUSED]={0}, ok=1;
  if(!PyArg_ParseTuple(args,"OOOOOOdOLLOOO",&o[iORD],&o[iU],&o[iV],&o[iSR],&o[iSI],&o[iSL],
       &floor,&o[iSZ],&size_cap,&chunk,&o[oA],&o[oB],&o[oDL])) return NULL;
  for(int i=0;i<NUSED && ok;i++){
    if(i==iSZ && o[i]==Py_None) continue;
    const int flags = PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|(i>=oA ? PyBUF_WRITABLE : 0);
    if(PyObject_GetBuffer(o[i],&b[i],flags)<0){ ok=0; break; }
    have[i]=1;
    const char *f=b[i].format ? b[i].format : "B";
    /* int64 arrives as "l" or "q", int32 as "i" or "l", by platform */
    const int same = !strcmp(f,fmt[i])
        || (fmt[i][0]=='q' && !strcmp(f,"l") && b[i].itemsize==8)
        || (fmt[i][0]=='i' && !strcmp(f,"l") && b[i].itemsize==4);
    if(!same || b[i].ndim!=ndim[i]) ok=0;
  }
  Py_ssize_t count=0, nodes=0, K=0, nsh=0;
  if(ok){
    count=b[iORD].shape[0]; nodes=b[iU].shape[0]; K=b[iU].shape[1]; nsh=b[iSR].shape[0];
    ok = K>=1 && nsh>=1 && chunk>=2 && b[iV].shape[0]==nodes && b[iSR].shape[1]==K
         && b[iSI].shape[0]==nsh && b[iSI].shape[1]==K && b[iSL].shape[0]==nsh
         && (!have[iSZ] || b[iSZ].shape[0]==nodes)
         && b[oA].shape[0]>=count/2 && b[oB].shape[0]>=count/2 && b[oDL].shape[0]>=count/2;
  }
  if(ok){
    /* the nodes named exist, each once: a node in two pairs would overrun the outputs */
    const int64_t *ord=(const int64_t*)b[iORD].buf;
    char *seen=(char*)calloc((size_t)nodes+1,1);
    if(!seen){ for(int i=0;i<NUSED;i++) if(have[i]) PyBuffer_Release(&b[i]); return PyErr_NoMemory(); }
    for(Py_ssize_t i=0;i<count && ok;i++){
      ok = ord[i]>=0 && ord[i]<nodes && !seen[ord[i]];
      if(ok) seen[ord[i]]=1;
    }
    free(seen);
  }
  long long n=0;
  if(ok){
    Py_BEGIN_ALLOW_THREADS
    n=ap_tier0_match((const int64_t*)b[iORD].buf,(long long)count,(long long)nodes,
        (const float*)b[iU].buf,(const double*)b[iV].buf,(const float*)b[iSR].buf,
        (const float*)b[iSI].buf,(const int64_t*)b[iSL].buf,(long long)K,(long long)nsh,floor,
        have[iSZ] ? (const int32_t*)b[iSZ].buf : NULL,size_cap,chunk,
        (int32_t*)b[oA].buf,(int32_t*)b[oB].buf,(int64_t*)b[oDL].buf);
    Py_END_ALLOW_THREADS
  }
  for(int i=0;i<NUSED;i++) if(have[i]) PyBuffer_Release(&b[i]);
  if(!ok){
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_match: invalid buffer shapes, dtypes or indices");
    return NULL;
  }
  if(n<0) return PyErr_NoMemory();
  return PyLong_FromLongLong(n);
}

long long ap_tier0_pairs_within(
    const int32_t *offsets, long long nclusters, const int32_t *members, const uint8_t *valid,
    const float *U, const double *v, const float *sr, const float *si,
    const int64_t *shift_lags, long long K, long long nsh, double floor, int32_t *a,
    int32_t *b, int64_t *dl);                                           /* src/tier0_match.cc */
/* tier0_pairs_within(offsets, members, valid, U, v, Sr, Si, lags, floor, out_a, out_b, out_dl)
   -> count: the coherent pairs inside each cluster, best first (src/tier0_match.cc). */
static PyObject *M_tier0_pairs_within(PyObject *self,PyObject *args){
  (void)self;
  enum { iOF,iME,iVA,iU,iV,iSR,iSI,iSL,oA,oB,oDL, NUSED };
  static const char *fmt[NUSED]={"i","i","B","Zf","d","f","f","q","i","i","q"};
  static const int ndim[NUSED]={1,1,1,2,1,2,2,1,1,1,1};
  PyObject *o[NUSED];
  Py_buffer b[NUSED];
  double floor=0.0;
  int have[NUSED]={0}, ok=1;
  if(!PyArg_ParseTuple(args,"OOOOOOOOdOOO",&o[iOF],&o[iME],&o[iVA],&o[iU],&o[iV],&o[iSR],
       &o[iSI],&o[iSL],&floor,&o[oA],&o[oB],&o[oDL])) return NULL;
  for(int i=0;i<NUSED && ok;i++){
    const int flags = PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|(i>=oA ? PyBUF_WRITABLE : 0);
    if(PyObject_GetBuffer(o[i],&b[i],flags)<0){ ok=0; break; }
    have[i]=1;
    const char *f=b[i].format ? b[i].format : "B";
    /* int64 arrives as "l" or "q", int32 as "i" or "l", by platform */
    const int same = !strcmp(f,fmt[i])
        || (fmt[i][0]=='q' && !strcmp(f,"l") && b[i].itemsize==8)
        || (fmt[i][0]=='i' && !strcmp(f,"l") && b[i].itemsize==4);
    if(!same || b[i].ndim!=ndim[i]) ok=0;
  }
  Py_ssize_t ncl=0, nm=0, nodes=0, K=0, nsh=0;
  if(ok){
    ncl=b[iOF].shape[0]-1; nm=b[iME].shape[0]; nodes=b[iU].shape[0]; K=b[iU].shape[1];
    nsh=b[iSR].shape[0];
    ok = ncl>=0 && K>=1 && nsh>=1 && b[iVA].shape[0]==nodes && b[iV].shape[0]==nodes
         && b[iSR].shape[1]==K && b[iSI].shape[0]==nsh && b[iSI].shape[1]==K
         && b[iSL].shape[0]==nsh && b[oA].shape[0]>=nm/2 && b[oB].shape[0]>=nm/2
         && b[oDL].shape[0]>=nm/2;
  }
  if(ok){
    /* the offsets run through the members in order, and the members are nodes, each once */
    const int32_t *of=(const int32_t*)b[iOF].buf, *me=(const int32_t*)b[iME].buf;
    ok = of[0]==0 && of[ncl]==nm;
    for(Py_ssize_t c=0;c<ncl && ok;c++) ok = of[c]<=of[c+1];
    char *seen=(char*)calloc((size_t)nodes+1,1);
    if(!seen){ for(int i=0;i<NUSED;i++) if(have[i]) PyBuffer_Release(&b[i]); return PyErr_NoMemory(); }
    for(Py_ssize_t i=0;i<nm && ok;i++){
      ok = me[i]>=0 && me[i]<nodes && !seen[me[i]];
      if(ok) seen[me[i]]=1;
    }
    free(seen);
  }
  long long n=0;
  if(ok){
    Py_BEGIN_ALLOW_THREADS
    n=ap_tier0_pairs_within((const int32_t*)b[iOF].buf,(long long)ncl,(const int32_t*)b[iME].buf,
        (const uint8_t*)b[iVA].buf,(const float*)b[iU].buf,(const double*)b[iV].buf,
        (const float*)b[iSR].buf,(const float*)b[iSI].buf,(const int64_t*)b[iSL].buf,
        (long long)K,(long long)nsh,floor,(int32_t*)b[oA].buf,(int32_t*)b[oB].buf,
        (int64_t*)b[oDL].buf);
    Py_END_ALLOW_THREADS
  }
  for(int i=0;i<NUSED;i++) if(have[i]) PyBuffer_Release(&b[i]);
  if(!ok){
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_pairs_within: invalid buffer shapes, dtypes or indices");
    return NULL;
  }
  if(n<0) return PyErr_NoMemory();
  return PyLong_FromLongLong(n);
}

/* The buffers of a tier0_pass / tier0_pair_level call: n objects, formats fmt ("Zd"
   complex128, "d" float64, "q" int64, "i" int32) and dimensions ndim; those from index
   first_out on are written. Returns 1 with every buffer held, or 0 with none (an error is
   set unless the fault is a format or dimension: the caller then sets its own). */
static int tier0_buffers(PyObject **o, Py_buffer *b, int n, const char *const *fmt,
                         const int *ndim, int first_out){
  for(int i=0;i<n;i++){
    const int flags = PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|(i>=first_out ? PyBUF_WRITABLE : 0);
    int ok = PyObject_GetBuffer(o[i],&b[i],flags)==0;
    if(ok){
      const char *f=b[i].format ? b[i].format : "B";
      /* int64 arrives as "l" or "q", int32 as "i" or "l", by platform */
      ok = (!strcmp(f,fmt[i])
            || (fmt[i][0]=='q' && !strcmp(f,"l") && b[i].itemsize==8)
            || (fmt[i][0]=='i' && !strcmp(f,"l") && b[i].itemsize==4))
           && b[i].ndim==ndim[i];
      if(!ok) PyBuffer_Release(&b[i]);
    }
    if(!ok){
      for(int j=0;j<i;j++) PyBuffer_Release(&b[j]);
      return 0;
    }
  }
  return 1;
}

long long ap_tier0_pass(
    const double *C, const double *inv_sqrt_v, const double *v, const double *w,
    const double *exp_all, const float *shifts, const int64_t *shift_lags, long long K,
    long long R, long long nsh, long long half_span, const double *cur,
    const double *inv_sqrt_vc, const double *cur_v, const int64_t *cur_dl,
    const int32_t *cur_offsets, const int32_t *cur_members, long long nc, const int64_t *ca,
    const int64_t *cb, const int64_t *cdl, long long ncand, int steps, double alpha_floor,
    double *next, double *next_v, int64_t *next_dl, int32_t *next_offsets,
    int32_t *next_members, double *alphas, int64_t *reach);              /* src/tier0_pass.cc */
/* tier0_pass(C, inv_sqrt_v, v, w, exp_all, shifts, shift_lags, half_span, cur, inv_sqrt_vc,
              cur_v, cur_dl, cur_offsets, cur_members, ca, cb, cdl, steps, alpha_floor,
              next, next_v, next_dl, next_offsets, next_members, alphas) -> (count, reach)
   One pass of the shared-screener merging (src/tier0_pass.cc): the level's clusters and the
   candidate merges of two of them (ca, cb, the second lagged cdl) in, the next level out.
   Inputs: C (nt, K) complex128; inv_sqrt_v, v (nt) float64; w (K) float64; exp_all
   (2 R + 1, K) complex128; shifts (nsh, K) complex64 and shift_lags (nsh) int64; cur (nc, K)
   complex128; inv_sqrt_vc, cur_v (nc) float64; cur_dl (nc) int64; cur_offsets (nc + 1) and
   cur_members (nt) int32; ca, cb, cdl (ncand) int64. Written when count > 0: next (nc, K)
   complex128, next_v (nc) float64, next_dl (nc) int64, next_offsets (nc + 1) and
   next_members (nt) int32, the next level's nc - count clusters first; alphas (nt) float64,
   the templates' retentions, in and out. Returns the number of merges accepted and the
   next level's largest member lag. */
static PyObject *M_tier0_pass(PyObject *self,PyObject *args){
  (void)self;
  enum { iC,iIV,iV,iW,iEX,iSH,iSL,iCUR,iIVC,iCV,iCD,iCO,iCM,iCA,iCB,iCDL,
         oN,oNV,oND,oNO,oNM,oAL, NUSED };
  static const char *const fmt[NUSED]={"Zd","d","d","d","Zd","Zf","q","Zd","d","d","q","i","i",
                                       "q","q","q", "Zd","d","q","i","i","d"};
  static const int ndim[NUSED]={2,1,1,1,2,2,1,2,1,1,1,1,1,1,1,1, 2,1,1,1,1,1};
  PyObject *o[NUSED];
  Py_buffer b[NUSED];
  long long half_span=0;
  int steps=0;
  double alpha_floor=0.0;
  if(!PyArg_ParseTuple(args,"OOOOOOOLOOOOOOOOOidOOOOOO",&o[iC],&o[iIV],&o[iV],&o[iW],&o[iEX],
       &o[iSH],&o[iSL],&half_span,&o[iCUR],&o[iIVC],&o[iCV],&o[iCD],&o[iCO],&o[iCM],&o[iCA],
       &o[iCB],&o[iCDL],&steps,&alpha_floor,&o[oN],&o[oNV],&o[oND],&o[oNO],&o[oNM],&o[oAL]))
    return NULL;
  if(!tier0_buffers(o,b,NUSED,fmt,ndim,oN)){
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_pass: invalid buffer dtypes or dimensions");
    return NULL;
  }
  const Py_ssize_t nt=b[iC].shape[0], K=b[iC].shape[1], nlag=b[iEX].shape[0];
  const Py_ssize_t nsh=b[iSH].shape[0], nc=b[iCUR].shape[0], ncand=b[iCA].shape[0];
  int ok = K>=1 && nsh>=1 && (nlag&1) && half_span>=0 && steps>=0
       && b[iIV].shape[0]==nt && b[iV].shape[0]==nt && b[iW].shape[0]==K
       && b[iEX].shape[1]==K && b[iSH].shape[1]==K && b[iSL].shape[0]==nsh
       && b[iCUR].shape[1]==K && b[iIVC].shape[0]==nc && b[iCV].shape[0]==nc
       && b[iCD].shape[0]==nc && b[iCO].shape[0]==nc+1 && b[iCM].shape[0]==nt
       && b[iCB].shape[0]==ncand && b[iCDL].shape[0]==ncand
       && b[oN].shape[0]==nc && b[oN].shape[1]==K && b[oNV].shape[0]==nc
       && b[oND].shape[0]==nc && b[oNO].shape[0]==nc+1 && b[oNM].shape[0]==nt
       && b[oAL].shape[0]==nt;
  if(ok){
    /* the clusters partition templates, a candidate names two clusters, and a cluster is in
       at most one candidate; the shifts' lags are lags there are */
    const int32_t *co=(const int32_t*)b[iCO].buf, *cm=(const int32_t*)b[iCM].buf;
    const int64_t *ca=(const int64_t*)b[iCA].buf, *cb=(const int64_t*)b[iCB].buf;
    const int64_t *sl=(const int64_t*)b[iSL].buf;
    const long long R=(nlag-1)/2;
    char *seen=(char*)calloc((size_t)nc+1,1);
    if(!seen){ for(int i=0;i<NUSED;i++) PyBuffer_Release(&b[i]); return PyErr_NoMemory(); }
    ok = nc==0 || co[0]==0;
    for(Py_ssize_t c=0;c<nc && ok;c++) ok = co[c]<=co[c+1];
    if(ok && nc>0) ok = co[nc]<=nt;
    for(Py_ssize_t i=0;ok && nc>0 && i<co[nc];i++) ok = cm[i]>=0 && cm[i]<nt;
    for(Py_ssize_t g=0;g<ncand && ok;g++){
      ok = ca[g]>=0 && ca[g]<nc && cb[g]>=0 && cb[g]<nc && ca[g]!=cb[g]
           && !seen[ca[g]] && !seen[cb[g]];
      if(ok) seen[ca[g]]=seen[cb[g]]=1;
    }
    for(Py_ssize_t s=0;s<nsh && ok;s++) ok = sl[s]>=-R && sl[s]<=R;
    free(seen);
  }
  long long count=0;
  int64_t reach=0;
  if(ok){
    Py_BEGIN_ALLOW_THREADS
    count=ap_tier0_pass((const double*)b[iC].buf,(const double*)b[iIV].buf,
        (const double*)b[iV].buf,(const double*)b[iW].buf,(const double*)b[iEX].buf,
        (const float*)b[iSH].buf,(const int64_t*)b[iSL].buf,(long long)K,(long long)(nlag-1)/2,
        (long long)nsh,half_span,(const double*)b[iCUR].buf,(const double*)b[iIVC].buf,
        (const double*)b[iCV].buf,(const int64_t*)b[iCD].buf,
        (const int32_t*)b[iCO].buf,(const int32_t*)b[iCM].buf,(long long)nc,
        (const int64_t*)b[iCA].buf,(const int64_t*)b[iCB].buf,(const int64_t*)b[iCDL].buf,
        (long long)ncand,steps,alpha_floor,(double*)b[oN].buf,(double*)b[oNV].buf,
        (int64_t*)b[oND].buf,(int32_t*)b[oNO].buf,(int32_t*)b[oNM].buf,(double*)b[oAL].buf,
        &reach);
    Py_END_ALLOW_THREADS
  }
  for(int i=0;i<NUSED;i++) PyBuffer_Release(&b[i]);
  if(!ok){
    PyErr_SetString(PyExc_ValueError,"tier0_pass: invalid buffer shapes or indices");
    return NULL;
  }
  if(count<0) return PyErr_NoMemory();
  return Py_BuildValue("LL",count,(long long)reach);
}

long long ap_tier0_pair_level(
    const double *C, const double *inv_sqrt_v, const double *v, const double *w,
    const double *exp_all, long long nt, long long K, long long R, long long half_span,
    double rho_min, long long max_nc, const int32_t *pa, const int32_t *pb, const int64_t *pdl,
    long long npairs, double *level, double *level_v, int64_t *level_dl, int32_t *offsets,
    int32_t *members, double *alphas, int64_t *reach);                   /* src/tier0_pass.cc */
/* tier0_pair_level(C, inv_sqrt_v, v, w, exp_all, half_span, rho_min, max_nc, pa, pb, pdl,
                    level, level_v, level_dl, offsets, members, alphas) -> (nc, reach)
   The first level of the shared-screener merging (src/tier0_pass.cc): the templates' pairs
   (pa < pb int32, pdl int64: the second's lag against the first) made clusters of two where
   they are coherent enough, every other template a cluster of its own. Inputs as
   tier0_pass. Written when nc > 0: level (nt, K) complex128, level_v (nt) float64, level_dl
   (nt) int64, offsets (nt + 1) and members (nt) int32, the nc clusters first; alphas (nt)
   float64. Returns the number of clusters (0: no pair is kept, or more than max_nc clusters
   are left) and the largest pair lag. */
static PyObject *M_tier0_pair_level(PyObject *self,PyObject *args){
  (void)self;
  enum { iC,iIV,iV,iW,iEX,iPA,iPB,iPD, oL,oLV,oLD,oOF,oME,oAL, NUSED };
  static const char *const fmt[NUSED]={"Zd","d","d","d","Zd","i","i","q", "Zd","d","q","i","i","d"};
  static const int ndim[NUSED]={2,1,1,1,2,1,1,1, 2,1,1,1,1,1};
  PyObject *o[NUSED];
  Py_buffer b[NUSED];
  long long half_span=0, max_nc=0;
  double rho_min=0.0;
  if(!PyArg_ParseTuple(args,"OOOOOLdLOOOOOOOOO",&o[iC],&o[iIV],&o[iV],&o[iW],&o[iEX],&half_span,
       &rho_min,&max_nc,&o[iPA],&o[iPB],&o[iPD],&o[oL],&o[oLV],&o[oLD],&o[oOF],&o[oME],&o[oAL]))
    return NULL;
  if(!tier0_buffers(o,b,NUSED,fmt,ndim,oL)){
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_pair_level: invalid buffer dtypes or dimensions");
    return NULL;
  }
  const Py_ssize_t nt=b[iC].shape[0], K=b[iC].shape[1], nlag=b[iEX].shape[0];
  const Py_ssize_t npairs=b[iPA].shape[0];
  const long long R=(nlag-1)/2;
  int ok = K>=1 && (nlag&1) && half_span>=0
       && b[iIV].shape[0]==nt && b[iV].shape[0]==nt && b[iW].shape[0]==K && b[iEX].shape[1]==K
       && b[iPB].shape[0]==npairs && b[iPD].shape[0]==npairs
       && b[oL].shape[0]==nt && b[oL].shape[1]==K && b[oLV].shape[0]==nt && b[oLD].shape[0]==nt
       && b[oOF].shape[0]==nt+1 && b[oME].shape[0]==nt && b[oAL].shape[0]==nt;
  if(ok){
    /* a pair names two templates, the smaller first, a template is in at most one pair, and
       a pair's lag is a lag there is */
    const int32_t *pa=(const int32_t*)b[iPA].buf, *pb=(const int32_t*)b[iPB].buf;
    const int64_t *pd=(const int64_t*)b[iPD].buf;
    char *seen=(char*)calloc((size_t)nt+1,1);
    if(!seen){ for(int i=0;i<NUSED;i++) PyBuffer_Release(&b[i]); return PyErr_NoMemory(); }
    for(Py_ssize_t i=0;i<npairs && ok;i++){
      ok = pa[i]>=0 && pa[i]<pb[i] && pb[i]<nt && !seen[pa[i]] && !seen[pb[i]]
           && pd[i]>=-R && pd[i]<=R;
      if(ok) seen[pa[i]]=seen[pb[i]]=1;
    }
    free(seen);
  }
  long long nc=0;
  int64_t reach=0;
  if(ok){
    Py_BEGIN_ALLOW_THREADS
    nc=ap_tier0_pair_level((const double*)b[iC].buf,(const double*)b[iIV].buf,
        (const double*)b[iV].buf,(const double*)b[iW].buf,(const double*)b[iEX].buf,
        (long long)nt,(long long)K,R,half_span,rho_min,max_nc,(const int32_t*)b[iPA].buf,
        (const int32_t*)b[iPB].buf,(const int64_t*)b[iPD].buf,(long long)npairs,
        (double*)b[oL].buf,(double*)b[oLV].buf,(int64_t*)b[oLD].buf,(int32_t*)b[oOF].buf,
        (int32_t*)b[oME].buf,(double*)b[oAL].buf,&reach);
    Py_END_ALLOW_THREADS
  }
  for(int i=0;i<NUSED;i++) PyBuffer_Release(&b[i]);
  if(!ok){
    PyErr_SetString(PyExc_ValueError,"tier0_pair_level: invalid buffer shapes or indices");
    return NULL;
  }
  if(nc<0) return PyErr_NoMemory();
  return Py_BuildValue("LL",nc,(long long)reach);
}

/* Each group's shared screener (src/tier0_mwu.cc): a group in each vector lane, and the plain
   routine it reproduces bit for bit. Both return 0, or -1 when out of memory. */
int ap_tier0_mwu(const double *u, const int64_t *counts, const double *ref, const double *w,
                 long long nb, long long M, long long K, int steps, double *c_out,
                 double *ov_out);
int ap_tier0_mwu_plain(const double *u, const int64_t *counts, const double *ref,
                       const double *w, long long nb, long long M, long long K, int steps,
                       double *c_out, double *ov_out);

/* tier0_mwu(U, counts, ref, w, steps, c_out, ov_out, plain=0): the shared screener of each of
   nb groups, group g of counts[g] members (1 .. M), and its members' overlaps. U (nb, M, K)
   complex128, a group's members its first counts[g] rows; counts (nb) int64; ref (nb, K)
   complex128, w (K) float64; c_out (nb, K) complex128 and ov_out (nb, M) float64 (a group's
   first counts[g] entries) are written. plain=1 runs the one-group routine group by group:
   the same bytes, for the test that says so. */
static PyObject *M_tier0_mwu(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer u={0}, cn={0}, rf={0}, w={0}, co={0}, ov={0};
  PyObject *uo, *cno, *rfo, *wo, *coo, *ovo;
  int steps=0, plain=0, got=0, ok=1;
  if(!PyArg_ParseTuple(args,"OOOOiOO|i",&uo,&cno,&rfo,&wo,&steps,&coo,&ovo,&plain)) return NULL;
  if(PyObject_GetBuffer(uo,&u,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=1;
  if(ok){ if(PyObject_GetBuffer(cno,&cn,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=2; }
  if(ok){ if(PyObject_GetBuffer(rfo,&rf,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=3; }
  if(ok){ if(PyObject_GetBuffer(wo,&w,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=4; }
  if(ok){ if(PyObject_GetBuffer(coo,&co,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=5; }
  if(ok){ if(PyObject_GetBuffer(ovo,&ov,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=6; }
  Py_ssize_t nb=0, M=0, K=0;
  if(ok){
    /* int64 arrives as "l" or "q", by platform */
    ok = u.ndim==3 && cn.ndim==1 && rf.ndim==2 && w.ndim==1 && co.ndim==2 && ov.ndim==2 && steps>=0
         && u.itemsize==16 && strcmp(u.format,"Zd")==0 && rf.itemsize==16 && strcmp(rf.format,"Zd")==0
         && cn.itemsize==8 && (strcmp(cn.format,"q")==0 || strcmp(cn.format,"l")==0)
         && co.itemsize==16 && strcmp(co.format,"Zd")==0
         && w.itemsize==8 && strcmp(w.format,"d")==0 && ov.itemsize==8 && strcmp(ov.format,"d")==0;
    if(ok){
      nb=u.shape[0]; M=u.shape[1]; K=u.shape[2];
      ok = M>=1 && K>=1 && cn.shape[0]==nb && rf.shape[0]==nb && rf.shape[1]==K && w.shape[0]==K
           && co.shape[0]==nb && co.shape[1]==K && ov.shape[0]==nb && ov.shape[1]==M;
      for(Py_ssize_t g=0;g<nb && ok;g++){
        const int64_t c=((const int64_t*)cn.buf)[g];
        ok = c>=1 && c<=M;
      }
    }
  }
  if(ok && (plain ? ap_tier0_mwu_plain : ap_tier0_mwu)(
       (const double*)u.buf,(const int64_t*)cn.buf,(const double*)rf.buf,(const double*)w.buf,
       (long long)nb,(long long)M,(long long)K,steps,(double*)co.buf,(double*)ov.buf)!=0){
    ok=0; PyErr_NoMemory();
  }
  if(!ok){
    if(got>=1) PyBuffer_Release(&u);
    if(got>=2) PyBuffer_Release(&cn);
    if(got>=3) PyBuffer_Release(&rf);
    if(got>=4) PyBuffer_Release(&w);
    if(got>=5) PyBuffer_Release(&co);
    if(got>=6) PyBuffer_Release(&ov);
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_mwu: invalid buffer shapes, dtypes or counts");
    return NULL;
  }
  PyBuffer_Release(&u); PyBuffer_Release(&cn); PyBuffer_Release(&rf); PyBuffer_Release(&w);
  PyBuffer_Release(&co); PyBuffer_Release(&ov);
  Py_RETURN_NONE;
}

static PyMethodDef methods[]={
  {"backend",M_backend,METH_NOARGS,"backend() -> name of the selected kernel"},
  {"chain_candidates",M_chain_candidates,METH_VARARGS,"chain_candidates(S, Nc, low, lowv, last_order, last_val, splits, K, Nn, prune, useless, dsets) -> [(earlier thresholds, earlier reach, lasts)]: gatechain._chain_candidates's search"},
  {"simulate",M_simulate,METH_VARARGS,"simulate(scale, seed, row0, nrows, kmax, bands, bscale, fscale, tab, t, fi, spos, sval, soff, npos, nval, noff, keep_at=0) -> (signal counts, noise counts, rows done): the gate model's simulation, per statistic the running maximum's records of the noise alone and outward from a signal, to the first row whose records do not fit"},
  {"tier0_pair_scores",M_tier0_pair_scores,METH_VARARGS,"tier0_pair_scores(Ur, Ui, Sr, Si, v_c, floor, out_rho2, out_s): single-core shifted pair coherence over a chunk, exact where it reaches floor"},
  {"tier0_refine_lags",M_tier0_refine_lags,METH_VARARGS,"tier0_refine_lags(prod_ab, exp_all, pdl, R, half_span, out_dl, out_g): exact complex128 fine-lag refinement"},
  {"plan_best",M_plan_best,METH_VARARGS,"plan_best(cands, hws, first, later, refine, direct[, feed]) -> (cost, candidate, last) or None: the cheapest of a chain's candidate plans on a CostModel"},
  {"tier0_pairs_within",M_tier0_pairs_within,METH_VARARGS,"tier0_pairs_within(offsets, members, valid, U, v, Sr, Si, lags, floor, out_a, out_b, out_dl) -> count: the coherent pairs inside each cluster, best first"},
  {"tier0_match",M_tier0_match,METH_VARARGS,"tier0_match(...) -> count: the matching of a level's vectors into pairs, chunk by chunk"},
  {"tier0_pass",M_tier0_pass,METH_VARARGS,"tier0_pass(...) -> (count, reach): one pass of the shared-screener merging, a level's clusters and candidate merges in, the next level out"},
  {"tier0_pair_level",M_tier0_pair_level,METH_VARARGS,"tier0_pair_level(...) -> (nc, reach): the first level of the shared-screener merging, the templates' coherent pairs made clusters of two"},
  {"tier0_mwu",M_tier0_mwu,METH_VARARGS,"tier0_mwu(U, counts, ref, w, steps, c_out, ov_out, plain=0): each group's shared screener (mean or minimax) and its members' overlaps"},
  {"running_records",M_running_records,METH_VARARGS,"running_records(a, e0, dir, L, d0, pos, val) -> count or -1: the running maximum's records of a[e0], a[e0 + dir], ... (L values) as (distance i + d0, sqrt value), simulate's (src/records.cc)"},
  {"records_within",M_records_within,METH_VARARGS,"records_within(pos, val, off, reach, out, at=None): per row the value (and pos) of its last record within reach (gatechain's window maxima)"},
  {"xxh64",M_xxh64,METH_VARARGS,"xxh64(buffer, seed=0) -> int: XXH64 of a C-contiguous buffer's bytes"},
  {"vulkan_emit",M_vulkan_emit,METH_VARARGS,"vulkan_emit(cmd, fns u64[9+], ops u64, start, end) -> end: the Vulkan emitter of the shared command list: record resolved ops[start:end) into cmd (_vkcompute._VkNative)"},
  {"half_bits",M_half_bits,METH_VARARGS,"half_bits(src float32, dst 16-bit): dst[i] = src[i] as IEEE half bits, NumPy's float32 -> float16 cast"},
  {"gauss_fill",M_gauss_fill,METH_VARARGS,"gauss_fill(out float32, seed, offset): out[i] = standard normal draw offset + i of stream seed (src/gauss.cc)"},
  {"gauss_fill_rows",M_gauss_fill_rows,METH_VARARGS,"gauss_fill_rows(out float32 (rows, len), seed, offset, step, scale=None, keep=None): out[r, i] = draw offset + r * step + i of stream seed, times scale[i // 2] when given (simulate's fill, src/gauss.cc)"},
  {"l1d_bytes",M_l1d_bytes,METH_NOARGS,"l1d_bytes() -> the L1 data cache size the OS reports, or 0 if unknown"},
  {"l2_bytes",M_l2_bytes,METH_NOARGS,"l2_bytes() -> the per-core L2 cache size the OS reports, or 0 if unknown"},
  {"series_group",M_series_group,METH_VARARGS,"series_group(n, requested) -> the series group a hierarchical plan of size n runs"},
  {"gate16_max",M_gate16_max,METH_VARARGS,"gate16_max(N, data, templates, nt) -> bytes of nt float32 FP16 maxima (-1: not fired), or None"},
  {"price_direct",M_price_direct,METH_VARARGS,"price_direct(real_series=False, complex_taps=False) -> ticks per lag x tap of the direct refine's correlation"},
  {"gate16",M_gate16,METH_NOARGS,"gate16() -> whether new hierarchical plans run the FP16 first gate"},
  {"targets",M_targets,METH_NOARGS,"targets() -> names this build can run here"},
  {"set_target",M_set_target,METH_VARARGS,"set_target(name|None) -> narrow the choice"},
  {"pack_peaks",M_pack_peaks,METH_VARARGS,"pack_peaks(peaks, idx, val) -> copy into structured peaks"},
  {"assemble_peaks",M_assemble_peaks,METH_O,"assemble_peaks(jobs) -> (offsets, templates, samples, snr, block_starts, block_lengths): every job's peaks in one arena, from its calls' parts (device readbacks or host results), job by job ((calls, window starts or None, merge bin sizes); a call is (geometry, ((first block, part), ...))), with HMFTable.run's assembly"},
  {"device_peaks",M_device_peaks,METH_VARARGS,"device_peaks(readback, peaks=True) -> (flat, lags, values, refined, tier1, direct, fft, t0_checked): one device readback's peaks (bytearrays, flat order) and counters"},
  {"window_bin_keep",M_window_bin_keep,METH_VARARGS,"window_bin_keep(win_starts, binsize, t, s, v, keep, is_float) -> kept count, or -1 when not ordered by template then sample"},
  {"taps_to_spectra",M_taps_to_spectra,METH_VARARGS,"taps_to_spectra(taps, counts, n, max_taps, out_spectra, complex=False)"},
  {"_t2s_plans",M_t2s_plans,METH_NOARGS,"_t2s_plans() -> FFT plans taps_to_spectra has made (it keeps them per block length)"},
  {NULL,NULL,0,NULL}};
static struct PyModuleDef mod={PyModuleDef_HEAD_INIT,"matchedfilter._core",NULL,-1,methods};
PyMODINIT_FUNC PyInit__core(void){
  /* An MF_ISA that names no target of this build leaves the library without a back end:
     refuse at import, naming the targets, rather than fail later in a kernel call. Not
     ImportError, which a consumer would report as "not installed". */
  if(ap_isa_init()){
    PyObject *names=PyUnicode_FromString("");
    for(int i=0;names && i<ap_target_count();i++){
      PyObject *nx=PyUnicode_FromFormat("%U %s",names,ap_target_name(i));
      Py_DECREF(names); names=nx;
    }
    if(names){
      PyErr_Format(PyExc_ValueError,"MF_ISA=%s is not one of this build's targets:%U",
                   getenv("MF_ISA"),names);
      Py_DECREF(names);
    }
    return NULL;
  }
  if(PyType_Ready(&MFType)<0) return NULL;
  if(PyType_Ready(&HMFType)<0) return NULL;
  if(PyType_Ready(&RootType)<0) return NULL;
  if(PyType_Ready(&HMFTableType)<0) return NULL;
  if(PyType_Ready(&SpectrumStoreType)<0) return NULL;
  PyObject *m=PyModule_Create(&mod);
  if(!m) return NULL;
  Py_INCREF(&MFType);   PyModule_AddObject(m,"MF",(PyObject*)&MFType);
  Py_INCREF(&HMFType);  PyModule_AddObject(m,"HMF",(PyObject*)&HMFType);
  Py_INCREF(&RootType); PyModule_AddObject(m,"Root",(PyObject*)&RootType);
  Py_INCREF(&HMFTableType); PyModule_AddObject(m,"HMFTable",(PyObject*)&HMFTableType);
  Py_INCREF(&SpectrumStoreType); PyModule_AddObject(m,"SpectrumStore",(PyObject*)&SpectrumStoreType);
  return m;
}
