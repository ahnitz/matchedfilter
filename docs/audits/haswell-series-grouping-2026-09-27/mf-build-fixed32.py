from pathlib import Path
import shutil,subprocess,json
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study');cand=r/'fixed32-src'
shutil.copytree(r/'final-src',cand,dirs_exist_ok=True)
f=cand/'balanced-inl.h';s=f.read_text().replace('static AP_ALWAYS_INLINE void stageA_tail(', 'template<int FIXED=0>\nstatic AP_ALWAYS_INLINE void stageA_tail(')
s=s.replace('const int N2=p->N2; const int N1=p->N1; (void)N1;', 'const int N2=FIXED ? FIXED : p->N2; const int N1=FIXED ? FIXED : p->N1; (void)N1;')
s=s.replace('int eb=eidx(&p->eb,k2);','int eb=FIXED ? k2 : eidx(&p->eb,k2);')
needle='static void stageA_prod_gm(BP*p,const float*dr,const float*di,\n                           const float*tr,const float*ti){'
assert needle in s
new='''static void stageA_prod_32(BP*p,const float*dr,const float*di,
                            const float*tr,const float*ti){
  vf TR[AP_W],TI[AP_W],OR[AP_W],OI[AP_W];
  for(int g=0;g<32/AP_W;g++){
    const size_t gb=(size_t)g*32*AP_W;
    fftsr32_prod_unit(dr+gb,di+gb,tr+gb,ti+gb,p->bR,p->bI,p->sR,p->sI,1,AP_W);
    stageA_tail<32>(p,g,TR,TI,OR,OI,p->bR,p->bI);
  }
}
'''+needle+'''
  if constexpr (AP_W==8) {
    if(p->fuse==2) return stageA_prod_32(p,dr,di,tr,ti);
  }
'''
s=s.replace(needle,new)
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'fixed32-candidate',dirs_exist_ok=True)
commands=json.loads((r/'final-build-commands.json').read_text())
commands=[[x.replace('/final-src','/fixed32-src').replace('/final-kernel.o','/fixed32-kernel.o').replace('/final-candidate/','/fixed32-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'fixed32-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
