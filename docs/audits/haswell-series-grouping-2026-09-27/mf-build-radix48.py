from pathlib import Path
import shutil, subprocess, json,importlib.util
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';cand=r/'radix48-src'
shutil.copytree(r/'stride-src',cand,dirs_exist_ok=True)
spec=importlib.util.spec_from_file_location('mfgen',cand/'gen.py');gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
f=cand/'codelets-inl.h';s=f.read_text()
for name,prod,broadcast in (('fftsr32_unit',False,False),('fftsr32_prod_unit',True,False),('fftsr32_prod_unit_broadcast',True,True)):
 start=s.index('static inline int '+name+'(');brace=s.index('{',start);depth=1;end=brace+1
 while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
 block=gen.build(32,[4,8],name,prod=prod)
 if broadcast:block=gen.broadcast_codelet(block)
 block=block.replace('const long S,const long DS','const long ignored_S,const long ignored_DS').replace('const long S)','const long ignored_S)')
 brace=block.index('{');block=block[:brace+1]+('\n const long S=1,DS=AP_W;\n' if prod else '\n const long S=1;\n')+block[brace+1:]
 s=s[:start]+block+s[end:]
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'radix48-candidate',dirs_exist_ok=True)
commands=json.loads((r/'stride-build-commands.json').read_text())
commands=[[x.replace('/stride-src','/radix48-src').replace('/stride-kernel.o','/radix48-kernel.o').replace('/stride-candidate/','/radix48-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'radix48-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
