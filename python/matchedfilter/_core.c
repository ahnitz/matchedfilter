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
static PyObject *MF_set_platform_fft(MFObject *self,PyObject *args){
  int on; if(!PyArg_ParseTuple(args,"p",&on)) return NULL;
  return PyBool_FromLong(ap_mf_set_platform_fft(self->p,on)==0);
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
GUARDED(MFObject,MF_set_platform_fft)
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
  {"set_platform_fft",(PyCFunction)MF_set_platform_fft_g,METH_VARARGS,"set_platform_fft(on) -> True if correlate_series_continuous now runs through the platform FFT"},
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
                 int busy; /* a method is running (GUARDED) */ } HMFObject;

/* HMF(n, ndata, ntemplates, bands, series_group=8, k=0): a gate chain of coarse
   bands (strictly increasing), then the full refine. Thresholds come from Python. */
static int HMF_init(HMFObject *self,PyObject *args,PyObject *kw){
  if(self->p){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: filter already initialised"); return -1; }
  Py_ssize_t n; int nd,nt; PyObject *bands_obj; (void)kw;
  int group=8; Py_ssize_t k_bins=0;
  if(!PyArg_ParseTuple(args,"niiO|in",&n,&nd,&nt,&bands_obj,&group,&k_bins)) return -1;
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
  self->p = ap_hmf_create_chain((size_t)n,(size_t)self->k,nd,nt,bands,(int)nti,group);
  if(!self->p){ PyErr_Format(PyExc_ValueError,
      "no hierarchical plan for n=%zd k=%zd with this chain (bands must be supported "
      "powers of two, strictly increasing and < n)",n,self->k); return -1; }
  self->n=n; self->nd=nd; self->nt=nt; return 0;
}
static void HMF_dealloc(HMFObject *self){
  if(self->p) ap_hmf_destroy(self->p);
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
/* run_series_sparse(series, starts, wstart, wend, t0, nt, binsize, thr, cnt[i32 rows])
   -> (flat, index, value) as bytes: int64 flat positions in the (blocks, nt, bins) table,
   int64 bin indices and complex64 values of every peak, in C order. The engine runs
   sparse (ap_hmf_set_sparse): rows no tier passes write only cnt, and only rows with
   cnt > 0 are read back -- no pass over the dense table at either end. */
static PyObject *HMF_run_series_sparse(HMFObject *self,PyObject *args){
  Py_buffer bs,bst,bws,bwe,bcnt,bph={0};
  int t0,nt; Py_ssize_t binsize; double thr;
  PyObject *ph_arg=NULL;
  if(!PyArg_ParseTuple(args,"y*y*y*y*iindw*|O",&bs,&bst,&bws,&bwe,&t0,&nt,&binsize,&thr,&bcnt,
                       &ph_arg))
    return NULL;
  int nblocks; size_t nb; Py_ssize_t rows;
  PyObject *ret=NULL;
  ap_peak *pk=NULL;
  if(!phase_arg(ph_arg,&bph)) goto done;
  if(!series_shape_r(self->n,self->nt,t0,nt,binsize,self->real,&bs,&bst,&bws,&bwe,&bph,
                     &nblocks,&nb,&rows))
    goto done;
  if(bcnt.len/(Py_ssize_t)sizeof(int)<rows){
    PyErr_SetString(PyExc_ValueError,"counts buffer too small"); goto done; }
  if(nb>(size_t)PY_SSIZE_T_MAX/(size_t)rows){
    PyErr_SetString(PyExc_ValueError,"overflowing output shape"); goto done; }
  const Py_ssize_t need=rows*(Py_ssize_t)nb;
  if(need>PY_SSIZE_T_MAX/(Py_ssize_t)sizeof(ap_peak)){
    PyErr_SetString(PyExc_ValueError,"overflowing output shape"); goto done; }
  pk=reserve_peaks(&self->peaks,&self->peak_capacity,need);
  if(!pk) goto done;
  int tot;
  int *cnt=(int*)bcnt.buf;
  Py_BEGIN_ALLOW_THREADS
  ap_hmf_set_sparse(self->p,1);
  tot=ap_hmf_run_series(self->p,(const float*)bs.buf,series_samples(bs.len,self->real,self->real_stride),
                        (const size_t*)bst.buf,(const size_t*)bws.buf,
                        (const size_t*)bwe.buf,phase_of(&bph),nblocks,t0,nt,(size_t)binsize,
                        (float)thr,pk,cnt);
  ap_hmf_set_sparse(self->p,0);
  Py_END_ALLOW_THREADS
  if(tot<0){ PyErr_SetString(PyExc_RuntimeError,"matchedfilter: run_series failed"); goto done; }
  /* The engine already counts final peaks. Trust its int total only when the
     output shape bounds it; retain the recount for larger shapes. */
  Py_ssize_t m=tot;
  if(need>INT_MAX){
    m=0;
    for(Py_ssize_t r=0;r<rows;r++) if(cnt[r]>0)
      for(size_t b=0;b<nb;b++) if(pk[(size_t)r*nb+b].index>=0) m++;
  }
  if(m>need){ PyErr_SetString(PyExc_RuntimeError,"inconsistent sparse peak count"); goto done; }
  PyObject *fl=PyBytes_FromStringAndSize(NULL,m*8), *ix=PyBytes_FromStringAndSize(NULL,m*8),
           *vl=PyBytes_FromStringAndSize(NULL,m*8);
  if(!fl||!ix||!vl){ Py_XDECREF(fl);Py_XDECREF(ix);Py_XDECREF(vl); goto done; }
  if(m){ long long *F=(long long*)PyBytes_AS_STRING(fl), *I=(long long*)PyBytes_AS_STRING(ix);
    float *V=(float*)PyBytes_AS_STRING(vl);
    Py_ssize_t k=0;
    for(Py_ssize_t r=0;r<rows;r++) if(cnt[r]>0)
      for(size_t b=0;b<nb;b++){
        const ap_peak *q=&pk[(size_t)r*nb+b];
        if(q->index<0) continue;
        if(k>=m) goto bad_count;
        F[k]=(long long)((size_t)r*nb+b); I[k]=(long long)q->index;
        V[2*k]=q->re; V[2*k+1]=q->im; k++;
      }
    if(k!=m) goto bad_count;
  }
  ret=Py_BuildValue("(NNNi)",fl,ix,vl,tot);
  goto done;
bad_count:
  Py_DECREF(fl);Py_DECREF(ix);Py_DECREF(vl);
  PyErr_SetString(PyExc_RuntimeError,"inconsistent sparse peak count");
done:
  PyBuffer_Release(&bs);PyBuffer_Release(&bst);PyBuffer_Release(&bws);
  PyBuffer_Release(&bwe);PyBuffer_Release(&bcnt);
  phase_release(&bph);
  return ret;
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

/* set_taps(taps, counts): taps float32 (nt, stride) C-contiguous, counts int64 (nt,). */
static PyObject *HMF_set_taps(HMFObject *self,PyObject *args){
  Py_buffer bt,bc; Py_ssize_t stride;
  if(!PyArg_ParseTuple(args,"y*ny*",&bt,&stride,&bc)) return NULL;
  int r=-1;
  if(stride>0 && buf_holds(bt.len,self->nt,stride,(Py_ssize_t)sizeof(float))
     && bc.len>=(Py_ssize_t)self->nt*(Py_ssize_t)sizeof(int64_t))
    r=ap_hmf_set_taps(self->p,(const float*)bt.buf,(size_t)stride,(const int64_t*)bc.buf);
  PyBuffer_Release(&bt); PyBuffer_Release(&bc);
  if(r<0){ PyErr_SetString(PyExc_ValueError,"matchedfilter: bad taps (need nt rows of float32 "
                           "taps, int64 counts in [1, min(stride, n)])"); return NULL; }
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
static PyObject *HMF_set_platform_fft(HMFObject *self,PyObject *args){
  int on; if(!PyArg_ParseTuple(args,"p",&on)) return NULL;
  return PyBool_FromLong(ap_hmf_set_platform_fft(self->p,on)==0);
}
static PyObject *HMF_q15_stats(HMFObject *self,PyObject *unused){
  (void)unused; long passed=0; unsigned long long ticks=0;
  ap_hmf_q15_stats(self->p,&passed,&ticks);
  return Py_BuildValue("(iLK)",ap_hmf_get_q15(self->p),(long long)passed,ticks);
}
static PyObject *HMF_series_group(HMFObject *self,PyObject *unused){
  (void)unused; return PyLong_FromLong(ap_hmf_series_group(self->p));
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
GUARDED(HMFObject,HMF_set_platform_fft)
GUARDED(HMFObject,HMF_set_taps)
GUARDED(HMFObject,HMF_set_real_series)
GUARDED(HMFObject,HMF_set_direct)
GUARDED(HMFObject,HMF_direct_stats)
GUARDED(HMFObject,HMF_price_direct_pair)
GUARDED(HMFObject,HMF_set_direct_prices)
GUARDED(HMFObject,HMF_set_q15)
GUARDED(HMFObject,HMF_q15_stats)
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
GUARDED(HMFObject,HMF_thresholds)
GUARDED(HMFObject,HMF_series_ticks)
GUARDED(HMFObject,HMF_tier_stats)
GUARDED(HMFObject,HMF_tier_inputs)
static PyMethodDef HMF_methods[]={
  {"series_group",(PyCFunction)HMF_series_group_g,METH_NOARGS,"actual series block group"},
  {"set_platform_fft",(PyCFunction)HMF_set_platform_fft_g,METH_VARARGS,"set_platform_fft(on) -> True if block forwards now run through the platform FFT"},
  {"set_taps",(PyCFunction)HMF_set_taps_g,METH_VARARGS,"set_taps(taps float32 (nt, stride), stride, counts int64 (nt,)): each template's real FIR taps"},
  {"set_real_series",(PyCFunction)HMF_set_real_series_g,METH_VARARGS,"set_real_series(on, stride=1) -> True if run_series now reads real float32 series (half-size block transforms); stride 2 reads one lane of a complex series"},
  {"set_direct",(PyCFunction)HMF_set_direct_g,METH_VARARGS,"set_direct(on, halfwidth=1) -> True if survivors are now refined by direct correlation where cheaper"},
  {"direct_stats",(PyCFunction)HMF_direct_stats_g,METH_NOARGS,"direct refine counters and prices"},
  {"price_direct_pair",(PyCFunction)HMF_price_direct_pair_g,METH_NOARGS,"price_direct_pair() -> (ticks per lag x tap, ticks per transform pair) timed on this plan's kernels, or None"},
  {"set_direct_prices",(PyCFunction)HMF_set_direct_prices_g,METH_VARARGS,"set_direct_prices(lagtap, fftpair) -> True: the prices the direct-or-transform choice compares"},
  {"set_q15",(PyCFunction)HMF_set_q15_g,METH_VARARGS,"set_q15(on) -> True if the first tier now runs behind the Q15 screen"},
  {"q15_stats",(PyCFunction)HMF_q15_stats_g,METH_NOARGS,"q15_stats() -> (on, pairs passed to the float tier, screen ticks)"},
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
   "run_series_sparse(series,starts,wstart,wend,t0,nt,binsize,thr,cnt) -> (flat,index,value bytes,total)"},
  {"stats",(PyCFunction)HMF_stats_g,METH_NOARGS,"stats() -> (pairs, refined)"},
  {"chain",(PyCFunction)HMF_chain_g,METH_NOARGS,"chain() -> bands"},
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
                        uint64_t offset, uint64_t step, const float *scale);
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
/* gauss_fill_rows(out, seed, offset, step, scale=None): out float32 (rows, len) C-contiguous,
   out[r, i] = draw offset + r * step + i of stream seed, times scale[i // 2] (float32, at least
   (len + 1) // 2 of them) when given: simulate's fill (ap_gauss_fill_rows). */
static PyObject *M_gauss_fill_rows(PyObject *self,PyObject *args){
  (void)self; PyObject *o, *so=Py_None; unsigned long long seed, offset, step;
  if(!PyArg_ParseTuple(args,"OKKK|O",&o,&seed,&offset,&step,&so)) return NULL;
  Py_buffer b, sb={0}; int has_scale = so!=Py_None;
  if(PyObject_GetBuffer(o,&b,PyBUF_WRITABLE|PyBUF_C_CONTIGUOUS|PyBUF_FORMAT|PyBUF_ND)<0) return NULL;
  if(has_scale && PyObject_GetBuffer(so,&sb,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&b); return NULL; }
  const Py_ssize_t rows = b.ndim==2 ? b.shape[0] : 0, len = b.ndim==2 ? b.shape[1] : 0;
  if(!b.format || strcmp(b.format,"f")!=0 || b.itemsize!=4 || b.ndim!=2
     || (has_scale && (!sb.format || strcmp(sb.format,"f")!=0 || sb.itemsize!=4 || sb.len/4 < (len+1)/2))){
    PyBuffer_Release(&b); if(has_scale) PyBuffer_Release(&sb);
    PyErr_SetString(PyExc_TypeError,"gauss_fill_rows needs a C-contiguous float32 (rows, len) buffer and a float32 scale of (len + 1) // 2 or more");
    return NULL;
  }
  Py_BEGIN_ALLOW_THREADS
  ap_gauss_fill_rows((float*)b.buf,(size_t)len,(size_t)rows,(size_t)len,(uint64_t)seed,(uint64_t)offset,
                     (uint64_t)step,has_scale ? (const float*)sb.buf : NULL);
  Py_END_ALLOW_THREADS
  PyBuffer_Release(&b); if(has_scale) PyBuffer_Release(&sb);
  Py_RETURN_NONE;
}
/* A[e] = |g y[e] + d[e]|^2 for e < m (d NULL: |g y[e]|^2), y and d complex: simulate's
   statistics. One pass the compiler vectorises; on x86-64 ELF builds also for AVX2 and
   AVX-512, picked when loaded (the module is built for the baseline ISA). */
#if defined(__x86_64__) && defined(__ELF__) && defined(__GNUC__)
__attribute__((target_clones("avx512f","avx2","default")))
#endif
static float sr_power(const float *restrict y, const float *restrict d, float g, long long m, float *restrict A){
  /* the largest A, as a maximum of bit patterns: for non-negative floats they order as the
     values do, and an integer maximum vectorises where a float one (NaN rules) does not */
  uint32_t mx=0;
  if(d){
    for(long long e=0;e<m;e++){
      const float re=g*y[2*e]+d[2*e], im=g*y[2*e+1]+d[2*e+1];
      const float v=re*re+im*im; uint32_t u; memcpy(&u,&v,4);
      A[e]=v; mx = u>mx ? u : mx;
    }
  } else {
    for(long long e=0;e<m;e++){
      const float re=g*y[2*e], im=g*y[2*e+1];
      const float v=re*re+im*im; uint32_t u; memcpy(&u,&v,4);
      A[e]=v; mx = u>mx ? u : mx;
    }
  }
  float r; memcpy(&r,&mx,4); return r;
}
/* One statistic's running-maximum records outward from the signal (simulate): of the
   values a[e0], a[e0 + dir], ... (L of them), each exceeding all before it (the first always)
   as (distance i + d0 for the i-th, sqrt value), appended at pos[*k], val[*k] and *k advanced
   (src/records.cc). Returns 0, or -1 when the arrays (cap entries) are full. */
int ap_sim_records(const float *a, long long e0, int dir, long long L, long long d0,
                   int32_t *pos, float *val, long long *k, long long cap);
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
static PyObject *M_simulate(PyObject *self,PyObject *args){
  (void)self;
  PyObject *sco,*bo,*bso,*tbo,*to,*fio,*spo,*svo,*soo,*npo,*nvo,*noo; unsigned long long seed; long long row0,nrows,kmax; double fscale, keep_at=0.0;
  if(!PyArg_ParseTuple(args,"OKLLLOOdOOOOOOOOO|d",&sco,&seed,&row0,&nrows,&kmax,&bo,&bso,&fscale,&tbo,&to,&fio,&spo,&svo,&soo,&npo,&nvo,&noo,&keep_at)) return NULL;
  if(!PyTuple_Check(bo)||!PyTuple_Check(bso)){ PyErr_SetString(PyExc_TypeError,"simulate: bands and bscale must be tuples"); return NULL; }
  const Py_ssize_t nb=PyTuple_GET_SIZE(bo), ns=2*(1+nb);
  const int has_sig = tbo!=Py_None, has_noise = npo!=Py_None;
  if(nb<1||nb>31||PyTuple_GET_SIZE(bso)!=nb||nrows<1||row0<0||!(has_sig||has_noise)){
    PyErr_SetString(PyExc_ValueError,"simulate: one bscale per band, 1..31 bands, nrows >= 1, row0 >= 0, signal or noise outputs"); return NULL;
  }
  long long b[32]; float bs[32];
  for(Py_ssize_t i=0;i<nb;i++){ b[i]=PyLong_AsLongLong(PyTuple_GET_ITEM(bo,i)); bs[i]=(float)PyFloat_AsDouble(PyTuple_GET_ITEM(bso,i)); }
  if(PyErr_Occurred()) return NULL;
  Py_buffer sc,tb={0},tt={0},fib={0}; int gin=0, ok=1;
  Py_buffer *in[4]={&sc,&tb,&tt,&fib}; PyObject *io[4]={sco,tbo,to,fio};
  for(;gin<(has_sig?4:1);gin++) if(PyObject_GetBuffer(io[gin],in[gin],PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ ok=0; break; }
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
  for(Py_ssize_t i=0;i<nb && ok;i++) ok = b[i]>=1 && b[i]<=n && n%b[i]==0 && (i==0||b[i]>b[i-1]) && b[i]<=32768;
  if(ok && has_sig){
    const int *fi=(const int*)fib.buf; const long long *t=(const long long*)tt.buf;
    for(long long r=0;r<nrows;r++) if(fi[r]<0||fi[r]>=NF||t[r]<0||t[r]>=n){ ok=0; break; }
  }
  #define SIM_RELEASE() do{ \
    for(int s=0;s<sgot;s++){ PyBuffer_Release(&spb[s]); PyBuffer_Release(&svb[s]); PyBuffer_Release(&sob[s]); } \
    for(int s=0;s<ngot;s++){ PyBuffer_Release(&npb[s]); PyBuffer_Release(&nvb[s]); PyBuffer_Release(&nob[s]); } \
    for(int i=0;i<gin;i++) PyBuffer_Release(in[i]); }while(0)
  if(!ok){
    SIM_RELEASE();
    if(!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError,"simulate: scale float32 (n), 1 <= kmax <= n; bands ascending, dividing n, <= 32768; with a signal tab complex64 (NF, 1 + bands, n), t int64 in [0, n), fi int32 in [0, NF) (nrows), pos int32 per statistic and side, and per band for the noise; val float32 of pos's length, off int64 (nrows + 1)");
    return NULL;
  }
  /* the noise alone needs no bins past the widest band */
  const long long kfill = has_sig ? kmax : (kmax < b[nb-1] ? kmax : b[nb-1]);
  ap_plan *pf = has_sig ? ap_create((size_t)n) : NULL, *pl[32]={0}; ok = !has_sig || pf!=NULL;
  for(Py_ssize_t i=0;i<nb && ok;i++) if(!(pl[i]=ap_create((size_t)b[i]))) ok=0;
  /* rows are drawn SIM_ROWS at a time (ap_gauss_fill_rows: two blocks share a vector on
     AVX-512, and a row of n = 2048 reads one block) */
  enum { SIM_ROWS = 2 };
  const size_t bytes=((size_t)(2*n*4)+63)/64*64;
  float *X=(float*)aligned_alloc(64,SIM_ROWS*bytes), *Y=(float*)aligned_alloc(64,bytes),
        *A=(float*)aligned_alloc(64,bytes/2+64);
  long long ks[64]={0}, kn[32]={0}, done=nrows;
  if(ok && X && Y && A){
    const float *scale=(const float*)sc.buf, *tab=has_sig ? (const float*)tb.buf : NULL;
    const long long *tv=has_sig ? (const long long*)tt.buf : NULL; const int *fi=has_sig ? (const int*)fib.buf : NULL;
    const float fs=(float)fscale, keep2=(float)(keep_at*keep_at);
    Py_BEGIN_ALLOW_THREADS
    memset(X,0,SIM_ROWS*bytes);   /* bins past kfill stay empty */
    for(long long r=0;r<nrows;r++){
      long long ks0[64], kn0[32];   /* the counts before this row, should it not fit */
      memcpy(ks0,ks,(size_t)ns*sizeof *ks); memcpy(kn0,kn,(size_t)nb*sizeof *kn);
      int full=0;
      const float *Xr = X + (r % SIM_ROWS) * (bytes/4);
      if(r % SIM_ROWS == 0){
        const long long rows = nrows-r < SIM_ROWS ? nrows-r : SIM_ROWS;
        ap_gauss_fill_rows(X,bytes/4,(size_t)rows,(size_t)(2*kfill),(uint64_t)seed,(uint64_t)(2*(row0+r)*n),
                           (uint64_t)(2*n),scale);
      }
      int kept = 1;             /* with a signal: the row's fine maximum somewhere reaches keep_at */
      for(Py_ssize_t s = has_sig ? 0 : 1; s<=nb && !full; s++){
        const long long m = s==0 ? n : b[s-1];
        const float g = s==0 ? fs : bs[s-1];
        /* a transform only reads its input (backend.h), so the row's transforms all read Xr */
        ap_fft(s==0 ? pf : pl[s-1],Xr,Y,AP_BACKWARD);
        if(has_noise && s>0){
          /* the noise alone, lags 0 .. m-1 */
          const int q=(int)(s-1); long long *off=(long long*)nob[q].buf; off[r]=kn[q];
          sr_power(Y,NULL,g,m,A);
          if(ap_sim_records(A,0,1,m,0,(int32_t*)npb[q].buf,(float*)nvb[q].buf,&kn[q],nvb[q].len/4)<0){ full=1; break; }
        }
        if(!has_sig) continue;
        if(!kept){
          for(int side=0;side<2;side++){ const int q=(int)(2*s+side); ((long long*)sob[q].buf)[r]=ks[q]; }
          continue;
        }
        /* |noise + response| at lag js + e (mod m), e = 0 .. m-1: the response's table holds,
           per phase rho = t - js R, its values in that order (tab[f, s, rho m + e]) */
        const long long R = n/m, t=tv[r], js = t/R;
        const float *D = tab+(size_t)2*fi[r]*(1+nb)*n + (size_t)2*s*n + (size_t)2*(t - js*R)*m;
        const float m1=sr_power(Y+2*js,D,g,m-js,A), m2=sr_power(Y,D+2*(m-js),g,js,A+(m-js));
        if(s==0 && keep2>0.f){
          const float mx = m1>m2 ? m1 : m2;
          if(mx<keep2){
            /* no window keeps this draw: no records, and no band's signal pass */
            kept=0;
            for(Py_ssize_t q=0;q<ns;q++) ((long long*)sob[q].buf)[r]=ks[q];
            if(!has_noise) break;
            continue;
          }
        }
        for(int side=0;side<2;side++){
          const int q=(int)(2*s+side);
          long long *off=(long long*)sob[q].buf; off[r]=ks[q];
          /* right: distances 0 .. m-1 forward; left: lag js - e is A[m - e], e = 1 .. m-1 */
          if(ap_sim_records(A, side ? m-1 : 0, side ? -1 : 1, side ? m-1 : m, side ? 1 : 0,
                            (int32_t*)spb[q].buf, (float*)svb[q].buf, &ks[q], svb[q].len/4)<0){ full=1; break; }
        }
      }
      if(full){
        /* the row's records so far are dropped: rows [0, r) are the call's */
        memcpy(ks,ks0,(size_t)ns*sizeof *ks); memcpy(kn,kn0,(size_t)nb*sizeof *kn);
        done=r;
        break;
      }
    }
    if(has_sig) for(Py_ssize_t q=0;q<ns;q++) ((long long*)sob[q].buf)[done]=ks[q];
    if(has_noise) for(Py_ssize_t q=0;q<nb;q++) ((long long*)nob[q].buf)[done]=kn[q];
    Py_END_ALLOW_THREADS
  }
  free(X); free(Y); free(A);
  if(pf) ap_destroy(pf);
  for(Py_ssize_t i=0;i<nb;i++){ if(pl[i]) ap_destroy(pl[i]); }
  SIM_RELEASE();
  #undef SIM_RELEASE
  if(!ok || !X || !Y || !A){ PyErr_SetString(PyExc_MemoryError,"simulate: no FFT plan or buffer"); return NULL; }
  PyObject *so=Py_None, *no=Py_None; Py_INCREF(Py_None); Py_INCREF(Py_None);
  if(has_sig){ Py_DECREF(so); so=PyTuple_New(ns); for(Py_ssize_t q=0;q<ns;q++) PyTuple_SET_ITEM(so,q,PyLong_FromLongLong(ks[q])); }
  if(has_noise){ Py_DECREF(no); no=PyTuple_New(nb); for(Py_ssize_t q=0;q<nb;q++) PyTuple_SET_ITEM(no,q,PyLong_FromLongLong(kn[q])); }
  return Py_BuildValue("(NNL)",so,no,done);
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
/* gatechain._chain_candidates's search (see there): every (thresholds, reach) it considers,
   in its depth-first order. S (M, k) float32: the kept draws' coarse maxima of the chain's
   tiers; Nc (k, R) float32: the noise blocks the search can keep alive, by tier; low[i],
   lowv[i] (i < k - 1): tier i's K + 1 smallest kept-draw indices and values, ascending;
   lasto, lastv: the last tier's; splits: the budget shares tried per tier. A reach is the
   alive count over Nn as a double, the same float as Python's int division. */
typedef struct {
  int k, K, M, R, nsplit, prune; long long Nn; double useless;
  const float *S, *Nc; const long long *low[3]; const float *lowv[3];
  const long long *lasto; const float *lastv; int nlast; const double *splits;
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

static void cc_consider(cc_state *c, const double *prefix, int ndead, const int *alive, int nalive,
                        const double *fracs){
  const int rem=c->K-ndead;
  if(rem<0 || rem>=c->M-ndead) return;
  int at=-1;
  if(ndead){
    int seen=0;
    for(int j=0;j<c->nlast;j++){
      if(c->dead[c->lasto[j]]) continue;
      if(seen==rem){ at=j; break; }
      seen++;
    }
    if(at<0) return;
  } else {
    if(c->nlast<=rem) return;
    at=rem;
  }
  const float g=c->lastv[at];
  const double last=(double)cc_filter(c,c->k-1,g,alive,nalive,NULL)/(double)c->Nn;
  if(c->prune) for(int i=0;i<c->k-1;i++) if(fracs[i]>c->useless) return;
  PyObject *th=PyTuple_New(c->k), *re=PyTuple_New(c->k+1), *pair=NULL;
  if(!th||!re){ Py_XDECREF(th); Py_XDECREF(re); c->err=1; return; }
  for(int i=0;i<c->k-1;i++) PyTuple_SET_ITEM(th,i,PyFloat_FromDouble(prefix[i]));
  PyTuple_SET_ITEM(th,c->k-1,PyFloat_FromDouble((double)g));
  PyTuple_SET_ITEM(re,0,PyFloat_FromDouble(1.0));
  for(int i=0;i<c->k-1;i++) PyTuple_SET_ITEM(re,i+1,PyFloat_FromDouble(fracs[i]));
  PyTuple_SET_ITEM(re,c->k,PyFloat_FromDouble(last));
  pair=PyTuple_Pack(2,th,re); Py_DECREF(th); Py_DECREF(re);
  if(!pair || PyList_Append(c->out,pair)) c->err=1;
  Py_XDECREF(pair);
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
    cc_rec(c,i+1,prefix,remaining-share,ndead+nnew,c->alive[i+1],cnt,fracs);
    for(int j=0;j<cut;j++) if(c->dead[low[j]]==mark) c->dead[low[j]]=0;
  }
}

static PyObject *M_chain_candidates(PyObject *self,PyObject *args){
  (void)self;
  PyObject *So,*Nco,*lowo,*lowvo,*lao,*lvo,*spo; int K,prune; long long Nn; double useless;
  if(!PyArg_ParseTuple(args,"OOOOOOOiLpd",&So,&Nco,&lowo,&lowvo,&lao,&lvo,&spo,&K,&Nn,&prune,&useless)) return NULL;
  Py_buffer S,N,la,lv,lb[3],lvb[3]; int nlb=0;
  if(PyObject_GetBuffer(So,&S,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0) return NULL;
  if(PyObject_GetBuffer(Nco,&N,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); return NULL; }
  if(PyObject_GetBuffer(lao,&la,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); PyBuffer_Release(&N); return NULL; }
  if(PyObject_GetBuffer(lvo,&lv,PyBUF_C_CONTIGUOUS|PyBUF_FORMAT)<0){ PyBuffer_Release(&S); PyBuffer_Release(&N); PyBuffer_Release(&la); return NULL; }
  cc_state c; memset(&c,0,sizeof c);
  int ok = S.ndim==2 && S.itemsize==4 && !strcmp(S.format,"f") && N.ndim==2 && N.itemsize==4 && !strcmp(N.format,"f")
           && la.itemsize==8 && (!strcmp(la.format,"q")||!strcmp(la.format,"l")) && lv.itemsize==4 && !strcmp(lv.format,"f")
           && la.len/8==lv.len/4 && PyTuple_Check(lowo) && PyTuple_Check(lowvo) && PyTuple_Check(spo) && Nn>0 && K>=1;
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
  PyObject *out=NULL;
  if(ok){
    c.K=K; c.Nn=Nn; c.prune=prune; c.useless=useless; c.S=(const float*)S.buf; c.Nc=(const float*)N.buf;
    c.splits=splits; c.nsplit=nsplit;
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
  if(!ok && !PyErr_Occurred())
    PyErr_SetString(PyExc_TypeError,"chain_candidates: S float32 (M, k <= 4), Nc float32 (k, R), per earlier tier int64 indices and float32 values of K + 1, the last tier's, splits a tuple of floats, Nn > 0");
  return out;
}
static PyObject *M_l1d_bytes(PyObject *self,PyObject *args){
  (void)self; (void)args;
  return PyLong_FromSize_t(ap_l1d_bytes());
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

  float *in_buf = (float*)malloc(2 * (size_t)n * sizeof(float));
  if(!in_buf){
    ap_destroy(plan);
    PyBuffer_Release(&btaps); PyBuffer_Release(&bcnt); PyBuffer_Release(&bout);
    PyErr_NoMemory();
    return NULL;
  }

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
    memset(in_buf, 0, 2 * (size_t)n * sizeof(float));
    if(cplx){
      const float *row = taps + t * 2 * (size_t)max_taps;
      for(size_t i = 0; i < count - half; i++){
        in_buf[2 * i] = row[2 * (half + i)]; in_buf[2 * i + 1] = row[2 * (half + i) + 1];
      }
      for(size_t i = 0; i < half; i++){
        in_buf[2 * ((size_t)n - half + i)] = row[2 * i];
        in_buf[2 * ((size_t)n - half + i) + 1] = row[2 * i + 1];
      }
    } else {
    const float *row = taps + t * (size_t)max_taps;
    for(size_t i = 0; i < count - half; i++){
      in_buf[2 * i] = row[half + i];
    }
    for(size_t i = 0; i < half; i++){
      in_buf[2 * ((size_t)n - half + i)] = row[i];
    }
    }
    ap_fft(plan, in_buf, out + t * 2 * (size_t)n, AP_FORWARD);
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


/* forward_cost(n, reps) -> (engine s, platform s or -1): one block forward of n points as
   the hierarchical series does it (copy with 1/n, transform), best of reps, both ways. */
static double now_s(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+1e-9*t.tv_nsec; }
static PyObject *M_forward_cost(PyObject *self, PyObject *args){
  (void)self; Py_ssize_t n; int reps=9;
  if(!PyArg_ParseTuple(args,"n|i",&n,&reps)) return NULL;
  if(n<16||(n&(n-1))){ PyErr_SetString(PyExc_ValueError,"n must be a power of two >= 16"); return NULL; }
  if(!ap_supported((size_t)n)){
    PyErr_Format(PyExc_ValueError,"forward_cost: n=%zd is not a size the engine supports",n);
    return NULL;
  }
  ap_plan *fft=ap_create((size_t)n); ap_accel *a=ap_accel_create((size_t)n);
  float *src=malloc(2*n*sizeof(float)), *tmp=malloc(2*n*sizeof(float)), *out=malloc(2*n*sizeof(float));
  double bn=1e30, ba=1e30;
  if(!fft||!src||!tmp||!out){
    /* A plan or buffer that could not be allocated: no price, said so -- not 1e30 s,
       which a caller would read as "the engine is slow" and store. */
    free(src); free(tmp); free(out); ap_destroy(fft); ap_accel_destroy(a);
    return PyErr_NoMemory();
  }
  {
    Py_BEGIN_ALLOW_THREADS
    for(Py_ssize_t k=0;k<2*n;k++) src[k]=(float)((k*2654435761u)%1000)*1e-3f;
    const float inv=1.0f/(float)n;
    for(int r=0;r<reps;r++){
      double t0=now_s();
      for(int i=0;i<8;i++){ for(Py_ssize_t k=0;k<2*n;k++) tmp[k]=src[k]*inv; ap_fft(fft,tmp,out,AP_FORWARD); }
      double t1=now_s();
      if(a) for(int i=0;i<8;i++) ap_accel_forward(a,src,(size_t)n,inv,out);
      double t2=now_s();
      if((t1-t0)/8<bn) bn=(t1-t0)/8;
      if(a && (t2-t1)/8<ba) ba=(t2-t1)/8;
    }
    Py_END_ALLOW_THREADS
  }
  free(src); free(tmp); free(out); ap_destroy(fft); ap_accel_destroy(a);
  return Py_BuildValue("(dd)", bn, a ? ba : -1.0);
}


/* gate16_bound(N, data, templates, nt) -> float32 array of nt: the FP16 first gate's
   reported bound (ap_gate16_run, one data row, window [0, N)), or None where there is no
   FP16 gate. Measurement only (tools/gate_margin.py --gate cpu-g16). data: N complex64,
   templates: nt x N complex64, correlated as the tier does (templates conjugated at ingest). */
void *ap_gate16_create(size_t m, int nd, int nt);
void ap_gate16_destroy(void *g);
int ap_gate16_set_template(void *g, int t, const float *spec);
int ap_gate16_set_data(void *g, int d, const float *spec);
int ap_gate16_run(void *g, int d0, int nd, int t0, int nt, size_t ws, size_t we, ap_peak *out);
static PyObject *M_gate16_bound(PyObject *self, PyObject *args){
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
  } else { PyErr_SetString(PyExc_ValueError,"gate16_bound failed"); }
  free(pk); ap_gate16_destroy(g); PyBuffer_Release(&bd); PyBuffer_Release(&bt);
  return res;
}


static PyObject *M_price_direct(PyObject *self,PyObject *unused){
  (void)self; (void)unused;
  return PyFloat_FromDouble(ap_hmf_price_direct());
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

static PyMethodDef methods[]={
  {"backend",M_backend,METH_NOARGS,"backend() -> name of the selected kernel"},
  {"chain_candidates",M_chain_candidates,METH_VARARGS,"chain_candidates(S, Nc, low, lowv, last_order, last_val, splits, K, Nn, prune, useless) -> [(thresholds, reach)]: gatechain._chain_candidates's search"},
  {"simulate",M_simulate,METH_VARARGS,"simulate(scale, seed, row0, nrows, kmax, bands, bscale, fscale, tab, t, fi, spos, sval, soff, npos, nval, noff, keep_at=0) -> (signal counts, noise counts, rows done): the gate model's simulation, per statistic the running maximum's records of the noise alone and outward from a signal, to the first row whose records do not fit"},
  {"running_records",M_running_records,METH_VARARGS,"running_records(a, e0, dir, L, d0, pos, val) -> count or -1: the running maximum's records of a[e0], a[e0 + dir], ... (L values) as (distance i + d0, sqrt value), simulate's (src/records.cc)"},
  {"records_within",M_records_within,METH_VARARGS,"records_within(pos, val, off, reach, out, at=None): per row the value (and pos) of its last record within reach (gatechain's window maxima)"},
  {"gauss_fill",M_gauss_fill,METH_VARARGS,"gauss_fill(out float32, seed, offset): out[i] = standard normal draw offset + i of stream seed (src/gauss.cc)"},
  {"gauss_fill_rows",M_gauss_fill_rows,METH_VARARGS,"gauss_fill_rows(out float32 (rows, len), seed, offset, step, scale=None): out[r, i] = draw offset + r * step + i of stream seed, times scale[i // 2] when given (simulate's fill, src/gauss.cc)"},
  {"l1d_bytes",M_l1d_bytes,METH_NOARGS,"l1d_bytes() -> the L1 data cache size the OS reports, or 0 if unknown"},
  {"series_group",M_series_group,METH_VARARGS,"series_group(n, requested) -> the series group a hierarchical plan of size n runs"},
  {"forward_cost",M_forward_cost,METH_VARARGS,"forward_cost(n, reps=9) -> (engine s, platform s or -1) per block forward"},
  {"gate16_bound",M_gate16_bound,METH_VARARGS,"gate16_bound(N, data, templates, nt) -> bytes of nt float32 bounds (-1: not fired), or None"},
  {"price_direct",M_price_direct,METH_NOARGS,"price_direct() -> ticks per lag x tap of the direct refine's correlation"},
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
