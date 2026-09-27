import os,json,time
from pathlib import Path
import numpy as np
import matchedfilter as mf
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169')
z=np.load(r/'capture/hier-00.npz'); n=int(z['n_fft']); nt=int(z['nbatch'])
args=(z['series'],z['starts'],z['win_start'],z['win_end']); kw=dict(binsize=n,threshold=float(z['threshold']),raw=True)
plans={}; outputs={}
for name,cut in [('auto',None),('balanced','128')]:
 if cut is None: os.environ.pop('MF_PBMAX',None)
 else: os.environ['MF_PBMAX']=cut
 p=mf.HierarchicalFilter(n,1,nt,snr=float(z['threshold']),fd=float(z['fd']),band=1024,taps=8)
 p.set_reference(z['reference']); p.set_templates(z['templates'])
 if float(z['first_stage'])>0: p.set_first_stage(float(z['first_stage']))
 for _ in range(3): i,v=p.run_series(*args,**kw)
 outputs[name]=(i.copy(),v.copy()); plans[name]=p
os.environ.pop('MF_PBMAX',None)
np.testing.assert_array_equal(outputs['auto'][0],outputs['balanced'][0])
np.testing.assert_allclose(outputs['auto'][1],outputs['balanced'][1],rtol=1e-5,atol=1e-5)
samples={k:[] for k in plans}
for rep in range(31):
 for name in (list(plans) if rep%2==0 else list(reversed(plans))):
  t=time.perf_counter_ns(); i,v=plans[name].run_series(*args,**kw); samples[name].append((time.perf_counter_ns()-t)/1e6)
  np.testing.assert_array_equal(i,outputs[name][0]);np.testing.assert_array_equal(v,outputs[name][1])
ratios=np.array(samples['auto'])/samples['balanced']
out=dict(samples_ms=samples,median_ms={k:float(np.median(v)) for k,v in samples.items()},median_speedup=float(np.median(ratios)),wins=int((ratios>1).sum()),rounds=len(ratios))
(r/'results/opt-paired.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
