from pathlib import Path
import json,shutil,subprocess
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study');v='fusedcold'
shutil.copytree(r/'fusedpeak-src',r/(v+'-src'),dirs_exist_ok=True)
f=r/(v+'-src/codelets-inl.h');s=f.read_text();a=s.index('static AP_ALWAYS_INLINE void fft_peak_consider(');b=s.index('\n}',a)+2
helper='''static HWY_NOINLINE void fft_peak_update(vf rr,vf ii,vf m,long k,size_t ws,size_t we,int conj,ap_peak*out){
  float mv[AP_W],rv[AP_W],iv[AP_W];
  V_STOREU(mv,m); V_STOREU(rv,rr); V_STOREU(iv,ii);
  for(int l=0;l<AP_W;l++) if(k+l>=(long)ws && k+l<(long)we && mv[l]>out->magnitude){
    out->index=k+l;out->re=rv[l];out->im=conj?-iv[l]:iv[l];out->magnitude=mv[l];
  }
}
static AP_ALWAYS_INLINE void fft_peak_consider(vf rr,vf ii,long k,size_t ws,size_t we,int conj,ap_peak*out){
  if(k>=(long)we || k+AP_W<=(long)ws) return;
  vf m=V_FMADD(rr,rr,V_MUL(ii,ii));
  if(__builtin_expect(V_MASK_ANY(V_CMP_GT(m,V_SET1(out->magnitude))),0))
    fft_peak_update(rr,ii,m,k,ws,we,conj,out);
}'''
f.write_text(s[:a]+helper+s[b:])
shutil.copytree(r/'fusedpeak-candidate',r/(v+'-candidate'),dirs_exist_ok=True)
commands=json.loads((r/'fusedpeak-build-commands.json').read_text())
commands=[[x.replace('/fusedpeak-src','/'+v+'-src').replace('/fusedpeak-kernel.o','/'+v+'-kernel.o').replace('/fusedpeak-candidate/','/'+v+'-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/(v+'-build-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
