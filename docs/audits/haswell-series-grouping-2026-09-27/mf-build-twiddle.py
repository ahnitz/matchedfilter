from pathlib import Path
import shutil, subprocess, json
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';src=p/'src/matchedfilter';cand=r/'twiddle-src'
shutil.copytree(r/'sr32-src',cand,dirs_exist_ok=True)
f=cand/'balanced-inl.h';s=f.read_text().replace('vf *TLr,*TLi;', 'vf *TLr,*TLi;\n  vf *full_tr,*full_ti;')
needle='  return p;\n}\n\nvoid destroy'
assert needle in s
s=s.replace(needle,'''  if (N == 1024) {
    size_t count=(size_t)n1/AP_W*n2;
    p->full_tr=ap_alloc64(count*sizeof(vf));
    p->full_ti=ap_alloc64(count*sizeof(vf));
    for(size_t idx=0;idx<count;idx++) {
      int k2=idx%n2;
      vf sr=V_SET1(p->scg[2*idx]),si=V_SET1(p->scg[2*idx+1]);
      p->full_tr[idx]=V_FMSUB(sr,p->TLr[k2],V_MUL(si,p->TLi[k2]));
      p->full_ti[idx]=V_FMADD(sr,p->TLi[k2],V_MUL(si,p->TLr[k2]));
    }
  }
'''+needle)
s=s.replace('free(p->ser);free(p->scg);free(p);','free(p->ser);free(p->scg);free(p->full_tr);free(p->full_ti);free(p);')
old='''        vf SR=V_SET1(sc[2*t]),SI=V_SET1(sc[2*t+1]);
        vf tr=V_FMSUB(SR,p->TLr[k2],V_MUL(SI,p->TLi[k2]));
        vf ti=V_FMADD(SR,p->TLi[k2],V_MUL(SI,p->TLr[k2]));'''
assert old in s
s=s.replace(old,'''        vf tr,ti;
        if (p->full_tr) {
          tr=p->full_tr[(size_t)g*N2+k2];
          ti=p->full_ti[(size_t)g*N2+k2];
        } else {
          vf SR=V_SET1(sc[2*t]),SI=V_SET1(sc[2*t+1]);
          tr=V_FMSUB(SR,p->TLr[k2],V_MUL(SI,p->TLi[k2]));
          ti=V_FMADD(SR,p->TLi[k2],V_MUL(SI,p->TLr[k2]));
        }''')
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'twiddle-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sr32-build-commands.json').read_text())
commands=[[x.replace('/sr32-src','/twiddle-src').replace('/sr32-kernel.o','/twiddle-kernel.o').replace('/sr32-candidate/','/twiddle-candidate/') for x in c] for c in commands]
for cmd in commands: subprocess.run(cmd,check=True)
(r/'twiddle-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
