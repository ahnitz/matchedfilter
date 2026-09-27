from pathlib import Path
import shutil,subprocess,json,re
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study');cand=r/'inplace32-src'
shutil.copytree(r/'fixed32-src',cand,dirs_exist_ok=True)
f=cand/'codelets-inl.h';s=f.read_text();name='fftsr32_unit';start=s.index('static inline int '+name+'(');brace=s.index('{',start);depth=1;end=brace+1
while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
block=s[start:end].replace(name+'(',name+'_inplace(').replace('vf*restrict ar,vf*restrict ai','float*restrict ar,float*restrict ai')
block=re.sub(r'(ar|ai)\[S\*(\d+)\]=(\w+);',lambda m:'V_STOREU(%s+AP_W*%s,%s);'%m.groups(),block)
block=re.sub(r'(ar|ai)\[S\*(\d+)\]',lambda m:'V_LOADU(%s+AP_W*%s)'%m.groups(),block)
s=s[:end]+'\n'+block+'\n'+s[end:];f.write_text(s)
f=cand/'balanced-inl.h';s=f.read_text();needle='''  const int N1=p->N1; (void)p->N2; (void)exact;''';assert needle in s
s=s.replace(needle,needle+'''
  if constexpr (AP_W==8) {
    if(p->fuse==2 && p->ilay) {
      float *ar=p->ire+(size_t)b*32*AP_W;
      float *ai=p->iim+(size_t)b*32*AP_W;
      fftsr32_unit_inplace(ar,ai,p->sR,p->sI,1);
      *RR=(vf*)ar; *RI=(vf*)ai;
      return;
    }
  }
''');f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'inplace32-candidate',dirs_exist_ok=True)
commands=json.loads((r/'fixed32-build-commands.json').read_text())
commands=[[x.replace('/fixed32-src','/inplace32-src').replace('/fixed32-kernel.o','/inplace32-kernel.o').replace('/fixed32-candidate/','/inplace32-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'inplace32-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
