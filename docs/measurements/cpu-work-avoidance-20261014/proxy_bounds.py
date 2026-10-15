#!/usr/bin/env python3
"""Offline feasibility of a certified screen based on shared coarse-filter subspaces.

This is an experiment harness, not a filtering implementation or throughput benchmark.
It uses actual bank taps and a per-top reference profile with synthetic Gaussian spectral
blocks. See the adjacent README for mathematical bounds and modeling limits. Run with
one BLAS thread on an otherwise idle core; the checked-in result used CPU 12:

  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 12 python proxy_bounds.py \
      --bank BANK.hdf --profiles PROFILES.npz --output proxy_bounds.json

The block length, band, rank choices, and reference gate match the recorded experiment.
No package, bank, profile, or runtime cost file is modified.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import h5py
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'python'))
from matchedfilter import gatechain

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--bank', type=Path, required=True)
parser.add_argument('--profiles', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--top', type=int, default=4)
parser.add_argument('--blocks', type=int, default=32)
parser.add_argument('--seed', type=int, default=71)
args = parser.parse_args()
if args.blocks < 1 or args.top < 0 or args.seed < 0:
    parser.error('--blocks must be positive; --top and --seed must be nonnegative')
if not args.bank.is_file() or not args.profiles.is_file():
    parser.error('--bank and --profiles must be existing files')
if args.output.resolve() in (args.bank.resolve(), args.profiles.resolve()):
    parser.error('--output must differ from the input files')
bank, profiles = args.bank, args.profiles
N, B, K = 2048, 256, args.blocks
rng = np.random.default_rng(args.seed)
pf = np.load(profiles)
power = gatechain.rebin_profile(pf[f'top_{args.top}'], float(pf['delta_f']), 2048, N)
gate = gatechain.chain_thresholds(power, N, 6, .001, (256,512,1024), window=(192,1856))['thresholds'][0]
frac = power[:B].sum() / power.sum()
active = power[:B] > 0
X = rng.standard_normal((K,B)) + 1j*rng.standard_normal((K,B))
X[:,~active] = 0
Xnorm = np.linalg.norm(X, axis=1)
Xsplit = np.linalg.norm(X.reshape(K,16,16),axis=2)
aggregates = {}
geometry=[]
start=time.perf_counter()

def report(key, c, projection, basis, coeff, residual):
    # Exact projected maxima are deliberately an optimistic bound: their cost is ignored.
    yp = np.fft.ifft(X[:,None,:]*projection[None,:,:],axis=-1)*B
    projected_max = np.abs(yp).max(axis=-1)
    residual_norm = np.linalg.norm(residual,axis=-1)
    radius = Xnorm[:,None]*residual_norm[None,:]
    residual_split = np.linalg.norm(residual.reshape(len(c),16,16),axis=-1)
    radius_split = Xsplit@residual_split.T
    # The usable cheap bound needs one norm maximum per shared basis, not template outputs.
    ybasis = np.fft.ifft(X[:,None,:]*basis[None,:,:],axis=-1)*B
    basis_max = np.sqrt(np.sum(np.abs(ybasis)**2,axis=1)).max(axis=-1)
    cheap = basis_max[:,None]*np.linalg.norm(coeff,axis=-1)[None,:]
    a=aggregates.setdefault(key,dict(nt=0,nclusters=0,rank_work=0,oracle=0,oracle_split=0,cheap=0,cheap_split=0,radii=[],residual=[],bounds=[]))
    a['nt'] += len(c); a['nclusters']+=1; a['rank_work']+=len(basis)
    a['oracle'] += int(np.sum(projected_max+radius<gate))
    a['oracle_split'] += int(np.sum(projected_max+radius_split<gate))
    a['cheap'] += int(np.sum(cheap+radius<gate))
    a['cheap_split'] += int(np.sum(cheap+radius_split<gate))
    a['radii'].extend(radius.mean(axis=0).tolist()); a['residual'].extend(residual_norm.tolist())
    a['bounds'].extend((cheap+radius).mean(axis=0).tolist())

with h5py.File(bank) as f:
    top=f[f'fir_data/upper/{args.top}']; mids=top['fine_bank_index'][:]
    mid_fft_n = max(16384, 1 << (top['taps'].shape[1] - 1).bit_length())
    for i,m in enumerate(mids):
        g=f[f'fir_data/{m}']; taps=g['taps'][:]; cnt=g['actual_tap_count'][:]
        if int(cnt.max()) > N:
            parser.error('this experiment requires fine filters to fit N=2048')
        h=np.fft.fft(taps,n=N,axis=1)*np.exp(2j*np.pi*(cnt//2)[:,None]*np.arange(N)[None,:]/N)
        hm=np.fft.fft(top['taps'][i], n=mid_fft_n)[::mid_fft_n//N]
        cfull=h[:,:N//2]*(np.abs(hm[:N//2])*np.sqrt(power[:N//2]))[None,:]
        c=cfull[:,:B]/np.sqrt((np.abs(cfull)**2).sum(axis=1)*frac)[:,None]
        geometry.append(dict(mid=int(m),nt=len(c),tap_max=int(cnt.max()),norm_med=float(np.median(np.linalg.norm(c,axis=1)))))
        # Clusters are phase-invariant spherical farthest-first, then nearest-medoid.
        unit=c/np.linalg.norm(c,axis=1)[:,None]
        sim=np.abs(unit@unit.conj().T)**2
        for size in (0,32,16,8):
            if size==0:
                clusters=[np.arange(len(c))]
            else:
                ncenters=int(np.ceil(len(c)/size)); centers=[int(np.argmax(sim.sum(axis=1)))]; best=sim[:,centers[0]].copy()
                for _ in range(1,ncenters):
                    nxt=int(np.argmin(best)); centers.append(nxt); best=np.maximum(best,sim[:,nxt])
                assignment=sim[:,centers].argmax(axis=1)
                clusters=[np.flatnonzero(assignment==j) for j in range(ncenters)]
            for members in clusters:
                sub=c[members]
                _,_,vh=np.linalg.svd(sub,full_matrices=False)
                for rank in (1,2,4,8,16):
                    if rank>=len(sub): continue
                    basis=vh[:rank]; coeff=sub@basis.conj().T; projection=coeff@basis; residual=sub-projection
                    report(f'size{size}/r{rank}',sub,projection,basis,coeff,residual)
        print(f'mid {m} ({i+1}/{len(mids)}) done {time.perf_counter()-start:.1f}s',flush=True)

ntotal = sum(g['nt'] for g in geometry)
out=dict(bank=bank.name,bank_sha256=hashlib.sha256(bank.read_bytes()).hexdigest(),
         profiles=profiles.name,profiles_sha256=hashlib.sha256(profiles.read_bytes()).hexdigest(),
         top=args.top,seed=args.seed,blocks=K,n=N,band=B,threshold=gate,frac=float(frac),
         gate_calibration_window=[192,1856],screening_window=[0,B],
         cluster_method='phase-invariant farthest-first medoids; no lag alignment',
         total_templates=ntotal,geometry=geometry,results={})
for key,a in aggregates.items():
    n=a['nt']*K
    out['results'][key]={k:a[k]/n for k in ('oracle','oracle_split','cheap','cheap_split')}
    out['results'][key].update(templates=a['nt'],clusters=a['nclusters'],basis_transform_fraction=a['rank_work']/a['nt'],residual_quantiles=np.quantile(a['residual'],[.1,.5,.9]).tolist(),radius_quantiles=np.quantile(a['radii'],[.1,.5,.9]).tolist(),cheap_bound_quantiles=np.quantile(a['bounds'],[.1,.5,.9]).tolist())
    # Small groups with rank >= size retain their existing individual filter. Conditional
    # rates above are useful for diagnosis; these whole-bank rates include that fallback.
    out['results'][key]['coverage_fraction'] = a['nt']/ntotal
    out['results'][key]['whole_bank'] = {k:a[k]/(ntotal*K) for k in ('oracle','oracle_split','cheap','cheap_split')}
    out['results'][key]['whole_bank']['basis_transform_fraction'] = a['rank_work']/ntotal
args.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='geometry'},indent=2))
