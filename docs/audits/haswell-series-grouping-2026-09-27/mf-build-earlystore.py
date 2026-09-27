from pathlib import Path
import shutil, subprocess, json,re
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';cand=r/'earlystore-src'
shutil.copytree(r/'stride-src',cand,dirs_exist_ok=True)
f=cand/'codelets-inl.h';s=f.read_text()
for name in ('fftsr32_unit','fftsr32_prod_unit','fftsr32_prod_unit_broadcast'):
 start=s.index('static inline int '+name+'(');brace=s.index('{',start);depth=1;end=brace+1
 while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
 block=s[start:end];lines=block.splitlines();stores={};keep=[]
 for line in lines:
  m=re.fullmatch(r'\s*ar\[S\*(\d+)\]=(\w+); ai\[S\*\1\]=(\w+);',line)
  if m:stores[m[3]]=line
  else:keep.append(line)
 assert len(stores)==32
 out=[]
 for line in keep:
  out.append(line)
  for var,store in stores.items():
   if re.search(r'\b'+var+r'=',line):out.append(store)
 assert len(out)==len(lines)
 s=s[:start]+'\n'.join(out)+s[end:]
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'earlystore-candidate',dirs_exist_ok=True)
commands=json.loads((r/'stride-build-commands.json').read_text())
commands=[[x.replace('/stride-src','/earlystore-src').replace('/stride-kernel.o','/earlystore-kernel.o').replace('/stride-candidate/','/earlystore-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'earlystore-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
