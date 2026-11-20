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
  unsigned char *dead; int *alive[4]; int nalive[4]; PyObject *out; int err;
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
    for(int i=1;i<=c.k;i++) c.alive[i]=(int*)malloc(((size_t)c.R+1)*sizeof(int));
    out=PyList_New(0); c.out=out;
    int mem = c.dead && out; for(int i=1;i<=c.k;i++) mem = mem && c.alive[i];
    if(mem){
      double prefix[4], fracs[4];
      cc_rec(&c,0,prefix,1.0,0,NULL,0,fracs);
    } else c.err=1;
    free(c.dead); for(int i=1;i<=c.k;i++) free(c.alive[i]);
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

  ap_plan *plan = ap_create((size_t)n);
  if(!plan){
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_SetString(PyExc_RuntimeError, "failed to create FFT plan");
    return NULL;
  }

  float *in_buf = (float*)ap_alloc64(2 * (size_t)n * sizeof(float));
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

  free(in_buf);
  ap_destroy(plan);
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

/* plan_best(cands, hws, first, later, refine, direct) -> (cost, candidate, last) or None
   cands: the list gatechain._chain_candidates returns, (earlier thresholds, earlier reach,
   lasts) each, lasts a (threshold, reach) or None per half-width. hws: the half-widths, an
   int or None each. first: (cost per pair of the dense first tier, None) or (that, (the
   screen's cost per pair, its cost per pair passed, the screen's excess table, tie)).
   later: per later tier (its sparse table, its sparse table behind a screen). refine: the
   refine table. direct: None, or (base, per lag, lags per half-width step, fraction, None or
   (share, the last tier's sparse table)). A table is (log densities, values), tuples of
   floats. Returns the cheapest plan's cost and where it is (the first of equal costs), or
   None when no candidate has a last tier. */
PB_EXACT static PyObject *M_plan_best(PyObject *self,PyObject *args){
  PB_EXACT_BODY
  (void)self;
  PyObject *cands,*hws,*first,*later,*refine,*direct;
  if(!PyArg_ParseTuple(args,"O!O!O!O!OO",&PyList_Type,&cands,&PyTuple_Type,&hws,
                       &PyTuple_Type,&first,&PyTuple_Type,&later,&refine,&direct)) return NULL;
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
      const double c=c_prefix+f*r_cost;
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
                         float *r2, int32_t *bs);                       /* src/tier0.cc */
/* tier0_pair_scores(Ur, Ui, Sr, Si, v_c, out_rho2, out_s): single-core shifted pair coherence
   over an m_c-template chunk without multi-threaded BLAS wakeup overhead (src/tier0.cc). */
static PyObject *M_tier0_pair_scores(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer ur={0},ui={0},sr={0},si={0},vc={0},r2={0},bs={0};
  PyObject *uro,*uio,*sro,*sio,*vco,*r2o,*bso;
  if(!PyArg_ParseTuple(args,"OOOOOOO",&uro,&uio,&sro,&sio,&vco,&r2o,&bso)) return NULL;
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
  int rc;
  Py_BEGIN_ALLOW_THREADS
  rc=ap_tier0_pair_scores(Urp,Uip,Srp,Sip,Vcp,(long long)mc,(long long)len,(long long)nsh,
                          (float*)r2.buf,(int32_t*)bs.buf);
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
int ap_tier0_mwu(const double *u, const double *ref, const double *w, long long nb, long long m,
                 long long K, int steps, double *c_out, double *ov_out);
int ap_tier0_mwu_plain(const double *u, const double *ref, const double *w, long long nb,
                       long long m, long long K, int steps, double *c_out, double *ov_out);

/* tier0_mwu(U, ref, w, steps, c_out, ov_out, plain=0): the shared screener of each of nb groups
   of m members, and its members' overlaps. U (nb, m, K) complex128, ref (nb, K) complex128,
   w (K) float64; c_out (nb, K) complex128 and ov_out (nb, m) float64 are written. plain=1 runs
   the one-group routine group by group: the same bytes, for the test that says so. */
static PyObject *M_tier0_mwu(PyObject *self,PyObject *args){
  (void)self;
  Py_buffer u={0}, rf={0}, w={0}, co={0}, ov={0};
  PyObject *uo, *rfo, *wo, *coo, *ovo;
  int steps=0, plain=0, got=0, ok=1;
  if(!PyArg_ParseTuple(args,"OOOiOO|i",&uo,&rfo,&wo,&steps,&coo,&ovo,&plain)) return NULL;
  if(PyObject_GetBuffer(uo,&u,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=1;
  if(ok){ if(PyObject_GetBuffer(rfo,&rf,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=2; }
  if(ok){ if(PyObject_GetBuffer(wo,&w,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=3; }
  if(ok){ if(PyObject_GetBuffer(coo,&co,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=4; }
  if(ok){ if(PyObject_GetBuffer(ovo,&ov,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) ok=0; else got=5; }
  Py_ssize_t nb=0, m=0, K=0;
  if(ok){
    ok = u.ndim==3 && rf.ndim==2 && w.ndim==1 && co.ndim==2 && ov.ndim==2 && steps>=0
         && u.itemsize==16 && strcmp(u.format,"Zd")==0 && rf.itemsize==16 && strcmp(rf.format,"Zd")==0
         && co.itemsize==16 && strcmp(co.format,"Zd")==0
         && w.itemsize==8 && strcmp(w.format,"d")==0 && ov.itemsize==8 && strcmp(ov.format,"d")==0;
    if(ok){
      nb=u.shape[0]; m=u.shape[1]; K=u.shape[2];
      ok = m>=1 && K>=1 && rf.shape[0]==nb && rf.shape[1]==K && w.shape[0]==K
           && co.shape[0]==nb && co.shape[1]==K && ov.shape[0]==nb && ov.shape[1]==m;
    }
  }
  if(ok && (plain ? ap_tier0_mwu_plain : ap_tier0_mwu)(
       (const double*)u.buf,(const double*)rf.buf,(const double*)w.buf,(long long)nb,(long long)m,
       (long long)K,steps,(double*)co.buf,(double*)ov.buf)!=0){ ok=0; PyErr_NoMemory(); }
  if(!ok){
    if(got>=1) PyBuffer_Release(&u);
    if(got>=2) PyBuffer_Release(&rf);
    if(got>=3) PyBuffer_Release(&w);
    if(got>=4) PyBuffer_Release(&co);
    if(got>=5) PyBuffer_Release(&ov);
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_ValueError,"tier0_mwu: invalid buffer shapes or dtypes");
    return NULL;
  }
  PyBuffer_Release(&u); PyBuffer_Release(&rf); PyBuffer_Release(&w);
  PyBuffer_Release(&co); PyBuffer_Release(&ov);
  Py_RETURN_NONE;
}

/* A follow-up job's Python buffers, beside its TdJob (followup.h); pooled in the scratch. */
typedef struct {
  Py_buffer bser, bw, btr, bti, bspec;
  int has_bw, has_tr, has_ti;
} TdJobIn;

static void td_release_job_buffers(TdJobIn *jobs, size_t count){
  for(size_t i = 0; i < count; i++){
    if(jobs[i].has_tr) PyBuffer_Release(&jobs[i].btr);
    if(jobs[i].has_ti) PyBuffer_Release(&jobs[i].bti);
    PyBuffer_Release(&jobs[i].bspec);
    if(jobs[i].has_bw) PyBuffer_Release(&jobs[i].bw);
    PyBuffer_Release(&jobs[i].bser);
  }
}

static PyObject *M_td_followup_batch(PyObject *self, PyObject *args){
  (void)self;
  PyObject *seq_obj;
  if(!PyArg_ParseTuple(args, "O", &seq_obj)) return NULL;
  PyObject *seq = PySequence_Fast(seq_obj, "td_followup_batch expects a sequence of job tuples");
  if(!seq) return NULL;
  const Py_ssize_t nj_ss = PySequence_Fast_GET_SIZE(seq);
  const size_t nj = (size_t)nj_ss;

  TdBatchScratch *ws = td_bscr_acquire();
  if(!ws){ Py_DECREF(seq); return PyErr_NoMemory(); }
  if(nj && td_grow_raw((void**)&ws->jobs, &ws->jobs_cap, nj, sizeof(TdJob)) < 0){
    td_bscr_release(ws);
    Py_DECREF(seq);
    return PyErr_NoMemory();
  }
  if(nj && td_grow_raw(&ws->bufs, &ws->bufs_cap, nj, sizeof(TdJobIn)) < 0){
    td_bscr_release(ws);
    Py_DECREF(seq);
    return PyErr_NoMemory();
  }
  TdJob *jobs = ws->jobs;
  TdJobIn *jins = (TdJobIn*)ws->bufs;
  if(nj){ memset(jobs, 0, nj * sizeof(TdJob)); memset(jins, 0, nj * sizeof(TdJobIn)); }

  size_t parsed = 0;
  size_t total_blks = 0;
  int ok = 1;
  for(size_t j = 0; j < nj; j++){
    PyObject *item = PySequence_Fast_GET_ITEM(seq, (Py_ssize_t)j);
    PyObject *oser, *ow, *otr, *oti, *ospec;
    int s_kind = 0, aligned = 0, rate_one = 0, L = 0, spec_ready = 0;
    Py_ssize_t S_ss = 0, n_ss = 0, step_ss = 0, cbad_ss = 0, bs_ss = 0;
    float thr = 0.f;
    long long global_ti = 0;
    if(!PyArg_ParseTuple(item, "OinOnnnnpfpiOOOpL",
                         &oser, &s_kind, &S_ss, &ow, &n_ss, &step_ss, &cbad_ss, &bs_ss,
                         &aligned, &thr, &rate_one, &L, &otr, &oti, &ospec, &spec_ready,
                         &global_ti)){
      ok = 0; break;
    }
    TdJob *jb = &jobs[j];
    TdJobIn *ji = &jins[j];
    const int ser_flags = (s_kind == 2) ? PyBUF_STRIDES : PyBUF_C_CONTIGUOUS;
    if(PyObject_GetBuffer(oser, &ji->bser, ser_flags) < 0){ ok = 0; break; }
    if(PyTuple_CheckExact(ow) && PyTuple_GET_SIZE(ow) == 2){
      const long long v0 = PyLong_AsLongLong(PyTuple_GET_ITEM(ow, 0));
      const long long v1 = PyLong_AsLongLong(PyTuple_GET_ITEM(ow, 1));
      if(PyErr_Occurred()){ PyBuffer_Release(&ji->bser); ok = 0; break; }
      jb->single_w[0] = (int64_t)v0;
      jb->single_w[1] = (int64_t)v1;
      jb->W = jb->single_w;
      jb->nw = (v0 < v1) ? 1u : 0u;
      ji->has_bw = 0;
    } else {
      if(PyObject_GetBuffer(ow, &ji->bw, PyBUF_C_CONTIGUOUS) < 0){
        PyBuffer_Release(&ji->bser); ok = 0; break;
      }
      ji->has_bw = 1;
    }
    if(PyObject_GetBuffer(ospec, &ji->bspec, PyBUF_WRITABLE | PyBUF_C_CONTIGUOUS) < 0){
      if(ji->has_bw) PyBuffer_Release(&ji->bw);
      PyBuffer_Release(&ji->bser);
      ok = 0; break;
    }
    if(otr != Py_None){
      if(PyObject_GetBuffer(otr, &ji->btr, PyBUF_C_CONTIGUOUS) < 0){
        PyBuffer_Release(&ji->bspec);
        if(ji->has_bw) PyBuffer_Release(&ji->bw);
        PyBuffer_Release(&ji->bser);
        ok = 0; break;
      }
      ji->has_tr = 1;
    }
    if(oti != Py_None){
      if(PyObject_GetBuffer(oti, &ji->bti, PyBUF_C_CONTIGUOUS) < 0){
        if(ji->has_tr) PyBuffer_Release(&ji->btr);
        PyBuffer_Release(&ji->bspec);
        if(ji->has_bw) PyBuffer_Release(&ji->bw);
        PyBuffer_Release(&ji->bser);
        ok = 0; break;
      }
      ji->has_ti = 1;
    }
    parsed = j + 1;

    if(n_ss < 16 || (n_ss & (n_ss - 1)) || !ap_supported((size_t)n_ss)
       || S_ss < 0 || step_ss < 1 || cbad_ss < 0 || bs_ss < 1
       || (s_kind < 0 || s_kind > 2)
       || (ji->has_bw && (ji->bw.len % (2 * (Py_ssize_t)sizeof(int64_t)) != 0))
       || ji->bspec.len < n_ss * 2 * (Py_ssize_t)sizeof(float)){
      PyErr_SetString(PyExc_ValueError, "td_followup_batch: invalid parameters or buffer sizes");
      ok = 0; break;
    }
    if(s_kind == 2){
      if(ji->bser.ndim != 1 || ji->bser.itemsize != 4 || !ji->bser.strides
         || (ji->bser.strides[0] != 8 && ji->bser.strides[0] != 4)){
        PyErr_SetString(PyExc_ValueError, "td_followup_batch: invalid stride-2 float32 series view");
        ok = 0; break;
      }
      if(ji->bser.strides[0] == 8){
        if(!ji->bser.shape || ji->bser.shape[0] < S_ss){
          PyErr_SetString(PyExc_ValueError, "td_followup_batch: series buffer too small");
          ok = 0; break;
        }
        jb->cser_floats = S_ss > 0 ? (size_t)(2 * S_ss - 1) : 0u;
      } else {
        const Py_ssize_t min_bytes = S_ss > 0 ? (2 * S_ss - 1) * 4 : 0;
        if(ji->bser.len < min_bytes){
          PyErr_SetString(PyExc_ValueError, "td_followup_batch: series buffer too small");
          ok = 0; break;
        }
        jb->cser_floats = (size_t)(ji->bser.len / (Py_ssize_t)sizeof(float));
      }
    } else {
      const Py_ssize_t min_ser_bytes = S_ss == 0 ? 0 : (s_kind == 0 ? S_ss * 8 : S_ss * 4);
      if(ji->bser.len < min_ser_bytes){
        PyErr_SetString(PyExc_ValueError, "td_followup_batch: series buffer too small");
        ok = 0; break;
      }
      jb->cser_floats = (size_t)(ji->bser.len / (Py_ssize_t)sizeof(float));
    }
    const int tr_cplx = (ji->has_tr && !ji->has_ti && ji->btr.itemsize == 8) ? 1 : 0;
    const Py_ssize_t min_tr_bytes = (Py_ssize_t)L * (tr_cplx ? 8 : 4);
    if(!spec_ready && (!rate_one || !ji->has_tr || L < 1
       || ji->btr.len < min_tr_bytes
       || (ji->has_ti && ji->bti.len < (Py_ssize_t)L * 4))){
      PyErr_SetString(PyExc_ValueError, "td_followup_batch: unready spectrum requires valid taps");
      ok = 0; break;
    }
    if(ji->has_tr && ji->btr.len < min_tr_bytes){
      PyErr_SetString(PyExc_ValueError, "td_followup_batch: tr buffer too small");
      ok = 0; break;
    }
    if(ji->has_ti && ji->bti.len < (Py_ssize_t)L * 4){
      PyErr_SetString(PyExc_ValueError, "td_followup_batch: ti buffer too small");
      ok = 0; break;
    }

    jb->ser_f = (const float*)ji->bser.buf;
    jb->s_kind = s_kind;
    jb->S = (int64_t)S_ss;
    if(ji->has_bw){
      jb->W = (const int64_t*)ji->bw.buf;
      jb->nw = (size_t)(ji->bw.len / (2 * (Py_ssize_t)sizeof(int64_t)));
    }
    jb->n = (size_t)n_ss;
    jb->step = (int64_t)step_ss;
    jb->c_bad = (int64_t)cbad_ss;
    jb->bs = (size_t)bs_ss;
    jb->aligned = aligned ? 1 : 0;
    jb->thr = thr;
    memcpy(&jb->thr_bits, &thr, sizeof(uint32_t));
    jb->rate_one = rate_one ? 1 : 0;
    jb->L = L;
    jb->tr_cplx = tr_cplx;
    jb->tr = ji->has_tr ? (const float*)ji->btr.buf : NULL;
    jb->ti = ji->has_ti ? (const float*)ji->bti.buf : NULL;
    jb->spec = (float*)ji->bspec.buf;
    jb->spec_ready = spec_ready ? 1 : 0;
    jb->global_ti = (int64_t)global_ti;

    size_t nblk = 0;
    uint64_t tlags = 0;
    for(size_t w = 0; w < jb->nw; w++){
      const int64_t v0 = jb->W[2 * w], v1 = jb->W[2 * w + 1];
      if(v0 < 0 || v1 <= v0 || v1 > jb->S) continue;
      const int64_t fidx = v0 > jb->c_bad ? (v0 - jb->c_bad) / jb->step : 0;
      const int64_t fts = fidx * jb->step;
      const int64_t lim = jb->S < (v1 - jb->c_bad) ? jb->S : (v1 - jb->c_bad);
      if(fts >= lim) continue;
      const int64_t nb_w = (lim - 1 - fts) / jb->step + 1;
      const int64_t lts = fts + (nb_w - 1) * jb->step;
      const int64_t rs0 = v0 > (fts + jb->c_bad) ? v0 : (fts + jb->c_bad);
      const int64_t re_last = v1 < (lts + jb->c_bad + jb->step) ? v1 : (lts + jb->c_bad + jb->step);
      nblk += (size_t)nb_w;
      if(re_last > rs0) tlags += (uint64_t)(re_last - rs0);
    }
    jb->blk0 = total_blks;
    jb->nblocks = nblk;
    jb->total_lags = tlags;
    jb->mode_td = (jb->rate_one && jb->tr != NULL && jb->L >= 1 && (size_t)jb->L <= jb->n
                   && (int64_t)(jb->L / 2) <= jb->c_bad
                   && jb->c_bad + jb->step <= (int64_t)jb->n
                   && tlags > 0 && tlags * (uint64_t)jb->L <= 32768ULL) ? 1 : 0;
    total_blks += nblk;
  }

  if(!ok){
    td_release_job_buffers(jins, parsed);
    td_bscr_release(ws);
    Py_DECREF(seq);
    return NULL;
  }

  if(total_blks && td_grow_raw((void**)&ws->blks, &ws->blks_cap, total_blks, sizeof(TdBlk)) < 0){
    td_release_job_buffers(jins, parsed);
    td_bscr_release(ws);
    Py_DECREF(seq);
    return PyErr_NoMemory();
  }
  if(nj && (nj > ws->ng_cap || !ws->ngroups || !ws->jidx)){
    size_t nc = ws->ng_cap ? ws->ng_cap : 64u;
    while(nc < nj) nc *= 2u;
    TdNGroup *ng = (TdNGroup*)malloc(nc * sizeof(TdNGroup));
    size_t *ji = (size_t*)malloc(nc * sizeof(size_t));
    if(!ng || !ji){
      free(ng); free(ji);
      td_release_job_buffers(jins, parsed);
      td_bscr_release(ws);
      Py_DECREF(seq);
      return PyErr_NoMemory();
    }
    free(ws->ngroups); free(ws->jidx);
    ws->ngroups = ng; ws->jidx = ji; ws->ng_cap = nc;
  }
  TdBlk *blks = ws->blks;
  TdNGroup *ngroups = ws->ngroups;
  size_t *jidx_buf = ws->jidx;

  /* Populate per-job block layouts and compute total peak slots before releasing GIL. */
  size_t total_pk_slots = 0;
  size_t max_job_blks = 0;
  for(size_t j = 0; j < nj; j++){
    TdJob *jb = &jobs[j];
    ngroups[j] = (TdNGroup){jb->n, j};
    if(jb->nblocks > max_job_blks) max_job_blks = jb->nblocks;
    size_t cur = jb->blk0;
    int any_ph = 0;
    for(size_t w = 0; w < jb->nw; w++){
      const int64_t v0 = jb->W[2 * w], v1 = jb->W[2 * w + 1];
      if(v0 < 0 || v1 <= v0 || v1 > jb->S) continue;
      const int64_t fidx = v0 > jb->c_bad ? (v0 - jb->c_bad) / jb->step : 0;
      const int64_t fts = fidx * jb->step;
      const int64_t lim = jb->S < (v1 - jb->c_bad) ? jb->S : (v1 - jb->c_bad);
      if(fts >= lim) continue;
      const int64_t nb_w = (lim - 1 - fts) / jb->step + 1;
      for(int64_t bi = 0; bi < nb_w; bi++){
        const int64_t ts = fts + bi * jb->step;
        const int64_t bvt0 = ts + jb->c_bad;
        const int64_t rs = v0 > bvt0 ? v0 : bvt0;
        const int64_t re = v1 < (bvt0 + jb->step) ? v1 : (bvt0 + jb->step);
        size_t ws_b = (size_t)(rs - ts);
        size_t we_b = (size_t)(re - ts);
        if(ws_b > jb->n) ws_b = jb->n;
        if(we_b > jb->n) we_b = jb->n;
        const uint32_t ph = jb->aligned ? (uint32_t)((uint64_t)(rs - v0) % (uint64_t)jb->bs) : 0u;
        if(ph) any_ph = 1;
        const size_t nb = we_b > ws_b ? (we_b - ws_b + (size_t)ph + jb->bs - 1u) / jb->bs : 0u;
        blks[cur++] = (TdBlk){ts, ws_b, we_b, ph, nb, w, 0};
      }
    }
    jb->nblocks = cur - jb->blk0;
    jb->any_ph = any_ph;
    jb->pk_off = total_pk_slots;
    if(!any_ph && jb->bs < jb->n && jb->nblocks > 1){
      TdBlkOrd stack_ord[64];
      TdBlkOrd *ord = jb->nblocks <= 64 ? stack_ord
          : (TdBlkOrd*)malloc(jb->nblocks * sizeof(TdBlkOrd));
      if(!ord){
        td_release_job_buffers(jins, parsed);
        td_bscr_release(ws);
        Py_DECREF(seq);
        return PyErr_NoMemory();
      }
      for(size_t b = 0; b < jb->nblocks; b++) ord[b] = (TdBlkOrd){blks[jb->blk0 + b].nb, b};
      qsort(ord, jb->nblocks, sizeof(TdBlkOrd), cmp_blk_ord);
      size_t pko = total_pk_slots;
      for(size_t s = 0; s < jb->nblocks; s++){
        TdBlk *bk = &blks[jb->blk0 + ord[s].idx];
        bk->pk_dst = pko;
        pko += bk->nb;
      }
      jb->pk_cnt = pko - total_pk_slots;
      total_pk_slots = pko;
      if(ord != stack_ord) free(ord);
    } else {
      size_t pko = total_pk_slots;
      for(size_t b = 0; b < jb->nblocks; b++){
        TdBlk *bk = &blks[jb->blk0 + b];
        bk->pk_dst = pko;
        pko += bk->nb;
      }
      jb->pk_cnt = pko - total_pk_slots;
      total_pk_slots = pko;
    }
  }

  if((total_pk_slots && td_grow_raw((void**)&ws->peaks, &ws->peaks_cap, total_pk_slots, sizeof(ap_peak)) < 0)
     || (max_job_blks && td_grow_raw((void**)&ws->ord, &ws->ord_cap, max_job_blks, sizeof(size_t)) < 0)){
    td_release_job_buffers(jins, parsed);
    td_bscr_release(ws);
    Py_DECREF(seq);
    return PyErr_NoMemory();
  }
  ap_peak *all_peaks = ws->peaks;
  size_t *ord_scratch = ws->ord;

  /* Pre-allocate output bytearrays at upper-bound capacity so compaction writes in-place. */
  PyObject *offs_ba = PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)((nj + 1) * sizeof(int64_t)));
  PyObject *rdy_ba = PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)nj);
  PyObject *si_ba = PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)(total_pk_slots * sizeof(int64_t)));
  PyObject *snr_ba = PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)(total_pk_slots * 2 * sizeof(float)));
  PyObject *bs_ba = PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)(total_pk_slots * sizeof(int64_t)));
  if(!offs_ba || !rdy_ba || !si_ba || !snr_ba || !bs_ba){
    Py_XDECREF(offs_ba); Py_XDECREF(rdy_ba); Py_XDECREF(si_ba);
    Py_XDECREF(snr_ba); Py_XDECREF(bs_ba);
    td_release_job_buffers(jins, parsed);
    td_bscr_release(ws);
    Py_DECREF(seq);
    return NULL;
  }
  int64_t *offs_p = (int64_t*)PyByteArray_AS_STRING(offs_ba);
  unsigned char *rdy_p = (unsigned char*)PyByteArray_AS_STRING(rdy_ba);
  int64_t *si_base = (int64_t*)PyByteArray_AS_STRING(si_ba);
  float *snr_base = (float*)PyByteArray_AS_STRING(snr_ba);
  int64_t *bs_base = (int64_t*)PyByteArray_AS_STRING(bs_ba);

  int run_err = 0;
  size_t total_kept = 0;

  Py_BEGIN_ALLOW_THREADS
  run_err = td_followup_run(ws, jobs, nj, ngroups, jidx_buf, blks, total_blks, all_peaks,
                            ord_scratch, offs_p, rdy_p, si_base, snr_base, bs_base, &total_kept);
  Py_END_ALLOW_THREADS

  PyObject *ret = NULL;
  if(run_err){
    PyErr_SetString(PyExc_RuntimeError, "td_followup_batch: kernel execution or allocation failed");
  } else {
    int rsz_ok = 1;
    if(total_kept != total_pk_slots){
      if(PyByteArray_Resize(si_ba, (Py_ssize_t)(total_kept * sizeof(int64_t))) < 0
         || PyByteArray_Resize(snr_ba, (Py_ssize_t)(total_kept * 2 * sizeof(float))) < 0
         || PyByteArray_Resize(bs_ba, (Py_ssize_t)(total_kept * sizeof(int64_t))) < 0){
        rsz_ok = 0;
      }
    }
    PyObject *ti_ba = rsz_ok ? PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)(total_kept * sizeof(int64_t))) : NULL;
    PyObject *bl_ba = rsz_ok ? PyByteArray_FromStringAndSize(NULL, (Py_ssize_t)(total_kept * sizeof(int64_t))) : NULL;
    if(rsz_ok && ti_ba && bl_ba){
      int64_t *ti_p = (int64_t*)PyByteArray_AS_STRING(ti_ba);
      int64_t *bl_p = (int64_t*)PyByteArray_AS_STRING(bl_ba);
      for(size_t j = 0; j < nj; j++){
        const TdJob *jb = &jobs[j];
        const int64_t gti = jb->global_ti;
        const int64_t blen = (int64_t)jb->n;
        for(size_t k = 0; k < jb->hit_cnt; k++){
          ti_p[jb->hit_off + k] = gti;
          bl_p[jb->hit_off + k] = blen;
        }
      }
      ret = PyTuple_Pack(7, offs_ba, ti_ba, si_ba, snr_ba, bs_ba, bl_ba, rdy_ba);
    }
    Py_XDECREF(ti_ba);
    Py_XDECREF(bl_ba);
  }
  Py_DECREF(offs_ba); Py_DECREF(rdy_ba); Py_DECREF(si_ba);
  Py_DECREF(snr_ba); Py_DECREF(bs_ba);

  td_release_job_buffers(jins, parsed);
  td_bscr_release(ws);
  Py_DECREF(seq);
  return ret;
}

static PyMethodDef methods[]={
  {"backend",M_backend,METH_NOARGS,"backend() -> name of the selected kernel"},
  {"chain_candidates",M_chain_candidates,METH_VARARGS,"chain_candidates(S, Nc, low, lowv, last_order, last_val, splits, K, Nn, prune, useless, dsets) -> [(earlier thresholds, earlier reach, lasts)]: gatechain._chain_candidates's search"},
  {"simulate",M_simulate,METH_VARARGS,"simulate(scale, seed, row0, nrows, kmax, bands, bscale, fscale, tab, t, fi, spos, sval, soff, npos, nval, noff, keep_at=0) -> (signal counts, noise counts, rows done): the gate model's simulation, per statistic the running maximum's records of the noise alone and outward from a signal, to the first row whose records do not fit"},
  {"tier0_pair_scores",M_tier0_pair_scores,METH_VARARGS,"tier0_pair_scores(Ur, Ui, Sr, Si, v_c, out_rho2, out_s): single-core shifted pair coherence over a chunk"},
  {"tier0_refine_lags",M_tier0_refine_lags,METH_VARARGS,"tier0_refine_lags(prod_ab, exp_all, pdl, R, half_span, out_dl, out_g): exact complex128 fine-lag refinement"},
  {"plan_best",M_plan_best,METH_VARARGS,"plan_best(cands, hws, first, later, refine, direct) -> (cost, candidate, last) or None: the cheapest of a chain's candidate plans on a CostModel"},
  {"tier0_match",M_tier0_match,METH_VARARGS,"tier0_match(...) -> count: the matching of a level's vectors into pairs, chunk by chunk"},
  {"tier0_pass",M_tier0_pass,METH_VARARGS,"tier0_pass(...) -> (count, reach): one pass of the shared-screener merging, a level's clusters and candidate merges in, the next level out"},
  {"tier0_pair_level",M_tier0_pair_level,METH_VARARGS,"tier0_pair_level(...) -> (nc, reach): the first level of the shared-screener merging, the templates' coherent pairs made clusters of two"},
  {"tier0_mwu",M_tier0_mwu,METH_VARARGS,"tier0_mwu(U, ref, w, steps, c_out, ov_out, plain=0): each group's shared screener (mean or minimax) and its members' overlaps"},
  {"td_followup_batch",M_td_followup_batch,METH_VARARGS,"td_followup_batch(jobs) -> (offs, ti, si, snr, bs, bl, spec_ready): batched single-template CPU follow-ups"},
  {"running_records",M_running_records,METH_VARARGS,"running_records(a, e0, dir, L, d0, pos, val) -> count or -1: the running maximum's records of a[e0], a[e0 + dir], ... (L values) as (distance i + d0, sqrt value), simulate's (src/records.cc)"},
  {"records_within",M_records_within,METH_VARARGS,"records_within(pos, val, off, reach, out, at=None): per row the value (and pos) of its last record within reach (gatechain's window maxima)"},
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
  {"window_bin_keep",M_window_bin_keep,METH_VARARGS,"window_bin_keep(win_starts, binsize, t, s, v, keep, is_float) -> kept count, or -1 when not ordered by template then sample"},
  {"taps_to_spectra",M_taps_to_spectra,METH_VARARGS,"taps_to_spectra(taps, counts, n, max_taps, out_spectra, complex=False)"},
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
  PyObject *m=PyModule_Create(&mod);
  if(!m) return NULL;
  Py_INCREF(&MFType);   PyModule_AddObject(m,"MF",(PyObject*)&MFType);
  Py_INCREF(&HMFType);  PyModule_AddObject(m,"HMF",(PyObject*)&HMFType);
  Py_INCREF(&RootType); PyModule_AddObject(m,"Root",(PyObject*)&RootType);
  return m;
}
