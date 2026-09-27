import json
from pathlib import Path
import h5py
import numpy as np
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/results')
def read(p):
    with h5py.File(p) as f:
        d={k:v[:] for k,v in f['L1'].items() if isinstance(v,h5py.Dataset)}
    order=np.lexsort((d['end_time'],d['template_hash']))
    return {k:v[order] for k,v in d.items()}
b=read(r/'kernel-full-baseline-1.hdf')
result={}
for p in sorted(r.glob('kernel-full-*.hdf')):
    d=read(p)
    np.testing.assert_array_equal(d["template_hash"], b["template_hash"])
    np.testing.assert_array_equal(d["end_time"], b["end_time"])
    result[p.name]={'count':len(d['snr']), 'fields':{k:{'exact':bool(np.array_equal(v,b[k],equal_nan=True)), 'max_abs_difference':float(np.max(np.abs(v.astype(np.float64)-b[k].astype(np.float64))))} for k,v in d.items()}}
(r/'kernel-full-trigger-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
