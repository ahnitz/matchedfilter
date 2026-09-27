from pathlib import Path
import json,shutil,subprocess,re
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'isolated-src',r/'signxor-src',dirs_exist_ok=True)
f=r/'signxor-src/codelets-inl.h';s=f.read_text();counts={}
for name in ('fftsr32_unit','fftsr32_prod_unit','fftsr32_unit_inplace'):
 a=s.index('static inline int '+name+'(');b=s.index('\n}',a)+2
 block,count=re.subn(r'V_SUB\(Z,(\w+)\)',r'V_XOR(\1,V_SIGNMASK())',s[a:b]);counts[name]=count;s=s[:a]+block+s[b:]
f.write_text(s)
shutil.copytree(r/'isolated-candidate',r/'signxor-candidate',dirs_exist_ok=True)
commands=json.loads((r/'isolated-build-commands.json').read_text())
commands=[[x.replace('/isolated-src','/signxor-src').replace('/isolated-kernel.o','/signxor-kernel.o').replace('/isolated-candidate/','/signxor-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'signxor-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print(counts)
