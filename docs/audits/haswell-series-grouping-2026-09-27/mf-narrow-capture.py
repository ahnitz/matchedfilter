from pathlib import Path
import ctypes as C, importlib.util,json,os,statistics
import numpy as np
import matchedfilter as mf
from matchedfilter import _core
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169')
spec=importlib.util.spec_from_file_location('study',r/'kernel-study/tools/narrow_cpu/run.py');study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
bridge=study.build('avx2',r/'kernel-study/narrow-build')
with np.load(r/'capture/hier-00.npz',allow_pickle=False) as z:d={k:z[k] for k in z.files}
n=int(d['n_fft']);band=1024;nt=int(d['nbatch'])
core=C.CDLL(_core.__file__);v=C.c_void_p
study.bind(core,'ap_create',[C.c_size_t],v);study.bind(core,'ap_fft',[v,v,v,C.c_int]);study.bind(core,'ap_destroy',[v])
p=core.ap_create(n);assert p
spectra=np.empty((len(d['starts']),n),np.complex64);buf=np.zeros(n,np.complex64)
try:
 for j,start in enumerate(d['starts']):
  start=int(start);part=d['series'][start:start+n];buf.fill(0);buf[:len(part)]=part/np.float32(n)
  core.ap_fft(p,buf.ctypes.data,spectra[j].ctypes.data,-1)
finally:core.ap_destroy(p)
f=mf.HierarchicalFilter(n,1,nt,snr=float(d['threshold']),fd=float(d['fd']),band=band,taps=8)
f.set_reference(d['reference']);f.set_templates(d['templates'])
if float(d['first_stage'])>0:f.set_first_stage(float(d['first_stage']))
thr=float(f._coarse_value(band,required=True))
power=d['reference'].astype(np.float64);fraction=np.float32(power[:band].sum()/power.sum())
h=np.ascontiguousarray(d['templates'][:,:band].astype(np.complex128)/np.sqrt(float(fraction)),dtype=np.complex64)
data=np.ascontiguousarray(spectra[:,:band]);R=n//band
windows=np.stack([np.maximum(0,d['win_start']//R-1),np.minimum(band,(d['win_end']+R-1)//R)],axis=1)
records=[];values=[np.empty((len(data),nt),np.float32) for _ in range(2)]
plans=[]
try:
 for win in np.unique(windows,axis=0):
  rows=np.flatnonzero((windows==win).all(axis=1));x=np.ascontiguousarray(data[rows]);lo,hi=map(int,win)
  ref=study.Reference(bridge,band,len(rows),nt);cand=study.Candidate(bridge,band,len(rows),nt,9);plans.extend([ref,cand])
  for i,p in enumerate((ref,cand)):p.templates(h);p.data(x);values[i][rows]=p.run(lo,hi)
  for ingest in (0,1):
   times=[[],[]]
   for rd in range(21):
    for j in ((0,1) if rd%2==0 else (1,0)):
     if j==0:
      sec=bridge.reference_bench(C.cast(ref.lib.ap_mf_run,v),C.cast(ref.lib.ap_mf_set_data,v),ref.p,band,len(rows),nt,ref.d.ctypes.data,ref.out.ctypes.data,lo,hi,3,ingest)
     else:sec=bridge.narrow_bench(cand.p,cand.out.ctypes.data,lo,hi,3,ingest)
     times[j].append(sec)
   records.append(dict(window=[lo,hi],blocks=len(rows),ingest=bool(ingest),samples=times,paired_speedup=statistics.median(a/b for a,b in zip(*times))))
finally:
 for p in plans:p.close()
a,b=values;fa=a>=thr;fb=b>=thr
result=dict(threshold=thr,pairs=int(a.size),reference_fired=int(fa.sum()),candidate_fired=int(fb.sum()),unsafe_rejections=int(np.count_nonzero(fa&~fb)),extra_admissions=int(np.count_nonzero(~fa&fb)),max_relative_error=float(np.max(abs(b/np.maximum(a,1e-30)-1))),timings=records)
(r/'results/kernel-narrow-capture.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='timings'},flush=True)
for x in records:print({k:v for k,v in x.items() if k!='samples'},flush=True)
report=study.fdr(bridge,band,32768)
(r/'results/kernel-narrow-fdr.json').write_text(json.dumps(report,indent=2)+'\n')
print('FDR',report['modes']['q15-bfp-prequant'],flush=True)
